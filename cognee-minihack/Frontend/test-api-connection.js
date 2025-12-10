/**
 * Simple test script to verify the data API is running and accessible
 * Run with: node test-api-connection.js
 */

const http = require('http');

const API_BASE = 'http://localhost:8001';

function testEndpoint(path, name) {
  return new Promise((resolve, reject) => {
    console.log(`\nTesting ${name}...`);
    
    http.get(`${API_BASE}${path}`, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const json = JSON.parse(data);
            console.log(`✓ ${name} OK - ${json.length} records found`);
            console.log(`  First record:`, json[0] ? JSON.stringify(json[0]).substring(0, 100) + '...' : 'N/A');
            resolve(json);
          } catch (e) {
            reject(new Error(`Failed to parse JSON: ${e.message}`));
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}`));
        }
      });
    }).on('error', (err) => {
      reject(err);
    });
  });
}

async function runTests() {
  console.log('=' .repeat(60));
  console.log('Testing Data API Connection');
  console.log('=' .repeat(60));
  
  try {
    await testEndpoint('/invoices', 'Invoices Endpoint');
    await testEndpoint('/transactions', 'Transactions Endpoint');
    
    console.log('\n' + '='.repeat(60));
    console.log('✓ All tests passed!');
    console.log('='.repeat(60));
    console.log('\nThe data API is running correctly.');
    console.log('You can now start the frontend with: npm run dev');
    
  } catch (error) {
    console.log('\n' + '='.repeat(60));
    console.log('✗ Test failed!');
    console.log('='.repeat(60));
    console.log('\nError:', error.message);
    console.log('\nMake sure the data API is running:');
    console.log('  cd /Users/hrishikesh/Desktop/Finance/cognee-minihack');
    console.log('  source .venv/bin/activate');
    console.log('  python services/data.py');
    process.exit(1);
  }
}

runTests();

