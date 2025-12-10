import asyncio
import pathlib
import os
import json
from typing import Optional, Type, List
from uuid import NAMESPACE_OID, uuid5
from dataclasses import dataclass

from cognee.infrastructure.engine import DataPoint
from cognee.modules.graph.cognee_graph.CogneeGraphElements import Edge
from cognee.modules.retrieval.graph_completion_retriever import GraphCompletionRetriever
from cognee.tasks.storage import add_data_points
from cognee.modules.graph.utils import resolve_edges_to_text
from cognee.modules.graph.utils.convert_node_to_data_point import get_all_subclasses
from cognee.modules.retrieval.utils.brute_force_triplet_search import brute_force_triplet_search
from cognee.modules.retrieval.utils.completion import summarize_text
from cognee.modules.retrieval.utils.session_cache import (
    save_conversation_history,
    get_conversation_history,
)
from cognee.shared.logging_utils import get_logger
from cognee.modules.retrieval.utils.extract_uuid_from_node import extract_uuid_from_node
from cognee.modules.retrieval.utils.models import CogneeUserInteraction
from cognee.modules.engine.models.node_set import NodeSet
from cognee.infrastructure.databases.graph import get_graph_engine
from cognee.context_global_variables import session_user
from cognee.infrastructure.databases.cache.config import CacheConfig
from custom_generate_completion import generate_completion_with_user_prompt
from cognee.infrastructure.llm.prompts.render_prompt import render_prompt

logger = get_logger("GraphCompletionRetrieverWithUserPrompt")


@dataclass
class CompletionResult:
    """Result containing the answer and the source information used to generate it."""
    answer: str
    context_text: str
    triplets: List[Edge]
    
    def _get_node_display_name(self, node) -> str:
        """Extract a human-readable display name from a Node object."""
        if node is None:
            return "Unknown"
        
        # Try to get the name attribute first (more human-readable)
        name = None
        if hasattr(node, 'get_attribute'):
            name = node.get_attribute('name')
        
        # Fall back to ID if no name
        node_id = None
        if hasattr(node, 'id'):
            node_id = node.id
        
        # Return name if available, otherwise ID
        if name:
            return name
        if node_id:
            # Shorten UUID if it's a long one
            if len(str(node_id)) > 20:
                return str(node_id)[:8] + "..."
            return str(node_id)
        return str(node)
    
    def _get_relationship_type(self, edge) -> str:
        """Extract relationship type from an Edge object."""
        if hasattr(edge, 'get_attribute'):
            rel_type = edge.get_attribute('relationship_type')
            if rel_type:
                return rel_type
            rel_type = edge.get_attribute('type')
            if rel_type:
                return rel_type
        return "related_to"
    
    def get_sources_summary(self) -> str:
        """Returns a formatted summary of source triplets used."""
        if not self.triplets:
            return "No source information available."
        
        sources = []
        for i, edge in enumerate(self.triplets, 1):
            # Use the Edge methods to get source and destination nodes
            try:
                source_node = edge.get_source_node() if hasattr(edge, 'get_source_node') else None
                target_node = edge.get_destination_node() if hasattr(edge, 'get_destination_node') else None
            except Exception:
                source_node = None
                target_node = None
            
            source_name = self._get_node_display_name(source_node)
            target_name = self._get_node_display_name(target_node)
            relationship = self._get_relationship_type(edge)
            
            sources.append(f"  [{i}] {source_name} --({relationship})--> {target_name}")
        
        return "\n".join(sources)
    
    def _extract_node_info(self, node) -> dict:
        """Extract node information as a dictionary for visualization."""
        if node is None:
            return {"id": "unknown", "name": "Unknown", "type": "Unknown"}
        
        node_id = node.id if hasattr(node, 'id') else str(node)
        name = None
        node_type = "Entity"
        content = None
        
        # Safely extract attributes - check if key exists in attributes dict first
        if hasattr(node, 'attributes') and isinstance(node.attributes, dict):
            name = node.attributes.get('name')
            node_type = node.attributes.get('type', 'Entity')
            # Try multiple possible content fields
            content = (node.attributes.get('content') or 
                      node.attributes.get('description') or 
                      node.attributes.get('text') or "")
        
        return {
            "id": str(node_id),
            "name": name or str(node_id)[:30],
            "type": node_type or "Entity",
            "content": content or ""
        }
    
    def visualize_sources(self, output_path: str, title: str = "Query Sources") -> str:
        """
        Generate an HTML visualization of the sources/triplets used for this answer.
        
        Args:
            output_path: Path where the HTML file will be saved
            title: Title to display in the visualization
            
        Returns:
            The path to the generated HTML file
        """
        if not self.triplets:
            return None
        
        # Extract nodes and edges from triplets
        nodes_dict = {}  # Use dict to avoid duplicates
        edges_list = []
        
        for edge in self.triplets:
            try:
                source_node = edge.get_source_node() if hasattr(edge, 'get_source_node') else None
                target_node = edge.get_destination_node() if hasattr(edge, 'get_destination_node') else None
            except Exception:
                continue
            
            if source_node is None or target_node is None:
                continue
            
            # Extract node info
            source_info = self._extract_node_info(source_node)
            target_info = self._extract_node_info(target_node)
            
            # Add nodes to dict (deduplicates by ID)
            nodes_dict[source_info["id"]] = source_info
            nodes_dict[target_info["id"]] = target_info
            
            # Get relationship type
            relationship = self._get_relationship_type(edge)
            
            # Add edge
            edges_list.append({
                "source": source_info["id"],
                "target": target_info["id"],
                "relation": relationship
            })
        
        # Convert nodes dict to list
        nodes_list = list(nodes_dict.values())
        
        # Color map for node types
        color_map = {
            "Entity": "#5C10F4",
            "Transaction": "#00C8FF",
            "Vendor": "#FF6B6B",
            "Invoice": "#4ECDC4",
            "LineItem": "#45B7D1",
            "Product": "#96CEB4",
            "default": "#D8D8D8"
        }
        
        # Add colors to nodes
        for node in nodes_list:
            node["color"] = color_map.get(node.get("type", "default"), color_map["default"])
        
        # Generate HTML
        html_content = self._generate_visualization_html(nodes_list, edges_list, title)
        
        # Ensure directory exists
        dir_path = os.path.dirname(output_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_visualization_html(self, nodes: list, edges: list, title: str) -> str:
        """Generate the HTML content for the visualization."""
        
        def safe_json(obj):
            return json.dumps(obj).replace("</", "<\\/")
        
        html_template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>''' + title + '''</title>
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <style>
        body, html { 
            margin: 0; padding: 0; width: 100%; height: 100%; 
            overflow: hidden; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
            color: white; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        }
        svg { width: 100vw; height: 100vh; display: block; }
        .links line { stroke: rgba(255, 255, 255, 0.3); stroke-width: 2px; }
        .nodes circle { stroke: white; stroke-width: 2px; cursor: pointer; }
        .nodes circle:hover { stroke-width: 3px; filter: brightness(1.2); }
        .node-label { 
            font-size: 12px; font-weight: bold; fill: #F4F4F4; 
            text-anchor: middle; pointer-events: none; 
            text-shadow: 0 0 4px rgba(0,0,0,0.8);
        }
        .edge-label { 
            font-size: 10px; fill: #FFD700; 
            text-anchor: middle; pointer-events: none; 
            font-weight: bold;
            text-shadow: 0 0 3px rgba(0,0,0,0.9);
        }
        #title {
            position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
            font-size: 24px; font-weight: bold; color: #FFD700;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
            z-index: 1000;
        }
        #info-panel {
            position: fixed; right: 20px; top: 20px;
            width: 300px; max-height: calc(100vh - 40px);
            overflow: auto; background: rgba(30, 30, 50, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 215, 0, 0.3);
            border-radius: 12px; color: #F4F4F4;
            padding: 16px; z-index: 1100;
        }
        #info-panel h3 { margin: 0 0 12px 0; font-size: 16px; color: #FFD700; }
        #info-panel .content { font-size: 13px; line-height: 1.5; }
        #info-panel .label { color: #888; }
        #info-panel .value { color: #FFF; margin-left: 8px; }
        #stats {
            position: fixed; left: 20px; bottom: 20px;
            background: rgba(30, 30, 50, 0.9);
            padding: 12px 16px; border-radius: 8px;
            font-size: 14px; z-index: 1000;
        }
        #legend {
            position: fixed; left: 20px; top: 20px;
            background: rgba(30, 30, 50, 0.9);
            padding: 12px 16px; border-radius: 8px;
            font-size: 12px; z-index: 1000;
        }
        .legend-item { display: flex; align-items: center; margin: 4px 0; }
        .legend-color { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
    </style>
</head>
<body>
    <div id="title">''' + title + '''</div>
    <svg></svg>
    <div id="info-panel">
        <h3>Node Details</h3>
        <div class="content">Click on a node to see details</div>
    </div>
    <div id="stats">Nodes: ''' + str(len(nodes)) + ''' | Edges: ''' + str(len(edges)) + '''</div>
    <div id="legend"></div>
    <script>
        var nodes = ''' + safe_json(nodes) + ''';
        var links = ''' + safe_json(edges) + ''';
        
        var svg = d3.select("svg"),
            width = window.innerWidth,
            height = window.innerHeight;
        
        var container = svg.append("g");
        var infoPanel = d3.select('#info-panel .content');
        
        // Build legend from unique node types
        var types = [...new Set(nodes.map(n => n.type))];
        var colorMap = {};
        nodes.forEach(n => { colorMap[n.type] = n.color; });
        var legendHtml = types.map(t => 
            '<div class="legend-item"><div class="legend-color" style="background:' + colorMap[t] + '"></div>' + t + '</div>'
        ).join('');
        d3.select('#legend').html(legendHtml);
        
        var simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(50));
        
        var link = container.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter().append("line");
        
        var edgeLabels = container.append("g")
            .attr("class", "edge-labels")
            .selectAll("text")
            .data(links)
            .enter().append("text")
            .attr("class", "edge-label")
            .text(d => d.relation);
        
        var node = container.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("r", 25)
            .attr("fill", d => d.color)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("click", function(d) {
                var html = '<div><span class="label">Name:</span><span class="value">' + d.name + '</span></div>';
                html += '<div><span class="label">Type:</span><span class="value">' + d.type + '</span></div>';
                html += '<div><span class="label">ID:</span><span class="value" style="font-size:10px;word-break:break-all;">' + d.id + '</span></div>';
                if (d.content) {
                    html += '<div style="margin-top:8px;"><span class="label">Content:</span><div class="value" style="margin-top:4px;font-size:11px;opacity:0.9;">' + d.content.substring(0, 200) + (d.content.length > 200 ? '...' : '') + '</div></div>';
                }
                infoPanel.html(html);
            });
        
        var nodeLabels = container.append("g")
            .attr("class", "node-labels")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .attr("class", "node-label")
            .attr("dy", 4)
            .text(d => d.name.length > 15 ? d.name.substring(0, 15) + '...' : d.name);
        
        simulation.on("tick", function() {
            link.attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            edgeLabels
                .attr("x", d => (d.source.x + d.target.x) / 2)
                .attr("y", d => (d.source.y + d.target.y) / 2 - 8);
            
            node.attr("cx", d => d.x).attr("cy", d => d.y);
            nodeLabels.attr("x", d => d.x).attr("y", d => d.y);
        });
        
        var zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", function() { container.attr("transform", d3.event.transform); });
        svg.call(zoom);
        
        function dragstarted(d) {
            if (!d3.event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
        }
        function dragged(d) { d.fx = d3.event.x; d.fy = d3.event.y; }
        function dragended(d) {
            if (!d3.event.active) simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
        }
        
        window.addEventListener("resize", function() {
            width = window.innerWidth; height = window.innerHeight;
            simulation.force("center", d3.forceCenter(width / 2, height / 2));
            simulation.alpha(1).restart();
        });
    </script>
</body>
</html>'''
        return html_template


class GraphCompletionRetrieverWithUserPrompt(GraphCompletionRetriever):
    """
    Retriever for handling graph-based completion searches, with a given filename
    for the user prompt.

    This class inherits from the GraphCompletionRetriever and provides all of its methods,
    with get_completion being slightly modified.
    """

    def __init__(
        self,
        user_prompt_filename: str,
        system_prompt_path: str = "answer_simple_question.txt",
        system_prompt: Optional[str] = None,
        top_k: Optional[int] = 5,
        node_type: Optional[Type] = None,
        node_name: Optional[List[str]] = None,
        save_interaction: bool = False,
    ):
        """Initialize retriever with prompt paths and search parameters."""
        super().__init__(
            save_interaction = save_interaction,
            system_prompt_path = system_prompt_path,
            system_prompt = system_prompt,
            top_k = top_k if top_k is not None else 5,
            node_type = node_type,
            node_name = node_name,
        )
        self.user_prompt_filename = user_prompt_filename

    async def get_completion(
        self,
        query: str,
        context: Optional[List[Edge]] = None,
        session_id: Optional[str] = None,
    ) -> List[str]:
        """
        Generates a completion using graph connections context based on a query.

        Parameters:
        -----------

            - query (str): The query string for which a completion is generated.
            - context (Optional[Any]): Optional context to use for generating the completion; if
              not provided, context is retrieved based on the query. (default None)
            - session_id (Optional[str]): Optional session identifier for caching. If None,
              defaults to 'default_session'. (default None)

        Returns:
        --------

            - Any: A generated completion based on the query and context provided.
        """
        triplets = context

        if triplets is None:
            triplets = await self.get_context(query)

        context_text = await resolve_edges_to_text(triplets)

        cache_config = CacheConfig()
        user = session_user.get()
        user_id = getattr(user, "id", None)
        session_save = user_id and cache_config.caching

        user_prompt = render_prompt(
            filename=self.user_prompt_filename,
            context={"question": query, "context": context_text},
            base_directory=str(pathlib.Path(
            os.path.join(pathlib.Path(__file__).parent, "prompts")).resolve())
        )

        if session_save:
            conversation_history = await get_conversation_history(session_id=session_id)

            context_summary, completion = await asyncio.gather(
                summarize_text(context_text),
                generate_completion_with_user_prompt(
                    user_prompt=user_prompt,
                    system_prompt_path=self.system_prompt_path,
                    system_prompt=self.system_prompt,
                    conversation_history=conversation_history,
                ),
            )
        else:
            completion = await generate_completion_with_user_prompt(
                user_prompt=user_prompt,
                system_prompt_path=self.system_prompt_path,
                system_prompt=self.system_prompt,
            )

        if self.save_interaction and context and triplets and completion:
            await self.save_qa(
                question=query, answer=completion, context=context_text, triplets=triplets
            )

        if session_save:
            await save_conversation_history(
                query=query,
                context_summary=context_summary,
                answer=completion,
                session_id=session_id,
            )

        return [completion]

    async def get_completion_with_sources(
        self,
        query: str,
        context: Optional[List[Edge]] = None,
        session_id: Optional[str] = None,
    ) -> CompletionResult:
        """
        Generates a completion with source information for transparency.

        This method is similar to get_completion but returns a CompletionResult
        object that includes both the answer and the source context used to
        generate it.

        Parameters:
        -----------
            - query (str): The query string for which a completion is generated.
            - context (Optional[List[Edge]]): Optional context to use; if not
              provided, context is retrieved based on the query.
            - session_id (Optional[str]): Optional session identifier for caching.

        Returns:
        --------
            - CompletionResult: Object containing the answer, context text, and
              source triplets used to generate the answer.
        """
        triplets = context

        if triplets is None:
            triplets = await self.get_context(query)

        context_text = await resolve_edges_to_text(triplets)

        cache_config = CacheConfig()
        user = session_user.get()
        user_id = getattr(user, "id", None)
        session_save = user_id and cache_config.caching

        user_prompt = render_prompt(
            filename=self.user_prompt_filename,
            context={"question": query, "context": context_text},
            base_directory=str(pathlib.Path(
            os.path.join(pathlib.Path(__file__).parent, "prompts")).resolve())
        )

        if session_save:
            conversation_history = await get_conversation_history(session_id=session_id)

            context_summary, completion = await asyncio.gather(
                summarize_text(context_text),
                generate_completion_with_user_prompt(
                    user_prompt=user_prompt,
                    system_prompt_path=self.system_prompt_path,
                    system_prompt=self.system_prompt,
                    conversation_history=conversation_history,
                ),
            )
        else:
            completion = await generate_completion_with_user_prompt(
                user_prompt=user_prompt,
                system_prompt_path=self.system_prompt_path,
                system_prompt=self.system_prompt,
            )

        if self.save_interaction and context and triplets and completion:
            await self.save_qa(
                question=query, answer=completion, context=context_text, triplets=triplets
            )

        if session_save:
            await save_conversation_history(
                query=query,
                context_summary=context_summary,
                answer=completion,
                session_id=session_id,
            )

        return CompletionResult(
            answer=completion,
            context_text=context_text,
            triplets=triplets or []
        )
