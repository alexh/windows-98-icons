#!/usr/bin/env python3
"""
Embed Failed Icons Script
Generates embeddings for the 4 failed icons using transformers.js
"""

import json
import subprocess
import sys
import tempfile
import time
import threading
from queue import Queue
from pathlib import Path
import os

def create_embedding_server():
    """Create a Node.js server that processes embedding requests"""
    model_name = os.getenv('EMBEDDING_MODEL', 'Xenova/bge-base-en-v1.5')
    
    return f'''
const {{ pipeline }} = require('@xenova/transformers');
const readline = require('readline');

let embeddingPipeline = null;

async function initPipeline() {{
    if (!embeddingPipeline) {{
        console.log("🔄 Loading embedding model: {model_name}");
        embeddingPipeline = await pipeline(
            'feature-extraction',
            '{model_name}',
            {{
                quantized: true
            }});
        console.log("✅ Model loaded successfully!");
    }}
    return embeddingPipeline;
}}

async function generateEmbedding(text) {{
    try {{
        const pipeline = await initPipeline();
        const output = await pipeline(text, {{
            pooling: 'mean',
            normalize: true
        }});
        return Array.from(output.data);
    }} catch (error) {{
        console.error('Error generating embedding:', error);
        return null;
    }}
}}

const rl = readline.createInterface({{
    input: process.stdin,
    output: process.stdout
}});

console.log("🚀 Embedding server ready! Send text lines to embed:");

rl.on('line', async (input) => {{
    try {{
        const data = JSON.parse(input);
        const {{ id, text }} = data;
        
        console.log(`📝 Processing ID ${{id}}: ${{text.substring(0, 50)}}...`);
        const embedding = await generateEmbedding(text);
        
        if (embedding) {{
            console.log(`✅ SUCCESS ID ${{id}}: Generated ${{embedding.length}} dimensions`);
            process.stdout.write(JSON.stringify({{ id, embedding }}) + '\\\\n');
        }} else {{
            console.log(`❌ FAILED ID ${{id}}`);
            process.stdout.write(JSON.stringify({{ id, error: true }}) + '\\\\n');
        }}
    }} catch (error) {{
        console.error('Parse error:', error);
    }}
}});

rl.on('close', () => {{
    console.log('🛑 Embedding server shutting down');
    process.exit(0);
}});
'''

def setup_node_environment():
    temp_dir = tempfile.mkdtemp()
    server_script = Path(temp_dir) / "embed_server.js"
    package_json = Path(temp_dir) / "package.json"
    
    package_content = {
        "name": "embedding-server",
        "version": "1.0.0",
        "dependencies": {
            "@xenova/transformers": "^2.17.2"
        }
    }
    
    with open(package_json, 'w') as f:
        json.dump(package_content, f, indent=2)
    
    with open(server_script, 'w') as f:
        f.write(create_embedding_server())
    
    print("📦 Installing transformers.js...")
    result = subprocess.run(
        ['npm', 'install'], 
        cwd=temp_dir, 
        capture_output=True, 
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ npm install failed: {result.stderr}")
        raise Exception("npm install failed")
    
    print("✅ Environment setup complete!")
    return temp_dir, server_script

class EmbeddingServer:
    def __init__(self, script_path):
        self.script_path = script_path
        self.process = None
        self.response_queue = Queue()
        self.pending_requests = {}
        
    def start(self):
        print("🚀 Starting embedding server...")
        self.process = subprocess.Popen(
            ['node', str(self.script_path)],
            cwd=self.script_path.parent,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Start thread to read responses
        self.reader_thread = threading.Thread(target=self._read_responses)
        self.reader_thread.daemon = True
        self.reader_thread.start()
        
        # Wait for server to be ready
        time.sleep(2)
        print("✅ Server started!")
    
    def _read_responses(self):
        for line in iter(self.process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue
                
            print(f"📡 Server: {line}")
            
            # Try to parse JSON responses
            if line.startswith('{'):
                try:
                    response = json.loads(line)
                    if 'id' in response:
                        self.response_queue.put(response)
                except json.JSONDecodeError:
                    pass
    
    def generate_embedding(self, request_id, text):
        # Send request
        request = json.dumps({"id": request_id, "text": text})
        self.process.stdin.write(request + '\\n')
        self.process.stdin.flush()
        
        # Wait for response
        while True:
            response = self.response_queue.get()
            if response['id'] == request_id:
                return response.get('embedding') if 'error' not in response else None
    
    def close(self):
        if self.process:
            self.process.terminate()
            self.process.wait()

def main():
    print("🎯 Processing failed icons embeddings...")
    
    # Load the failed icons file
    with open('failed_icons_processed.json', 'r') as f:
        data = json.load(f)
    
    icons = data.get('processed_icons', [])
    print(f"📊 Found {len(icons)} failed icons to embed")
    
    # Setup environment
    temp_dir, server_script = setup_node_environment()
    
    # Start embedding server
    server = EmbeddingServer(server_script)
    server.start()
    
    try:
        start_time = time.time()
        completed = 0
        failed = 0
        
        for i, icon in enumerate(icons, 1):
            name = icon.get('name', 'unknown')
            searchable_text = icon.get('searchable_text', '')
            
            print(f"\\n📝 Processing {i}/{len(icons)}: {name}")
            
            embedding = server.generate_embedding(i, searchable_text)
            
            if embedding:
                # Add embedding to the icon data
                icon['embedding'] = embedding
                completed += 1
                print(f"  💾 Added embedding ({len(embedding)} dimensions)")
            else:
                failed += 1
                print(f"  ❌ Failed to embed")
        
        # Save updated data back to file
        print(f"\\n💾 Saving updated data to: failed_icons_processed.json")
        with open('failed_icons_processed.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        total_time = time.time() - start_time
        print(f"""
🎉 COMPLETED!
✅ Successfully embedded: {completed} icons
❌ Failed: {failed} icons
⏱️  Total time: {total_time:.2f} seconds
🚀 Average speed: {completed / total_time:.2f} embeddings/second
        """)
        
    finally:
        server.close()
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print("🧹 Cleaned up temporary files")

if __name__ == "__main__":
    main()