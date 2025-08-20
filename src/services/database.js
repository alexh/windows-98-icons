let SQL = null

export async function loadDatabase() {
  try {
    // Initialize sql.js if not already done
    if (!SQL) {
      SQL = await window.initSqlJs({
        locateFile: file => `https://unpkg.com/sql.js@1.8.0/dist/${file}`
      })
    }

    // Load the database file
    const response = await fetch('./icons.db')
    if (!response.ok) {
      throw new Error(`Failed to load database: ${response.status}`)
    }

    const dbBuffer = await response.arrayBuffer()
    const db = new SQL.Database(new Uint8Array(dbBuffer))
    
    return db
  } catch (error) {
    console.error('Error loading database:', error)
    throw error
  }
}

export async function searchIcons(db, query) {
  if (!db) {
    throw new Error('Database not initialized')
  }

  try {
    if (!query || query.trim() === '') {
      // Return all icons if no search query
      const sql = `
        SELECT 
          name,
          filename,
          local_path,
          description,
          width,
          height
        FROM icons 
        ORDER BY name
      `
      return executeQuery(db, sql, [])
    } else {
      // Try vector search first, fall back to text search
      try {
        const vectorResults = await performVectorSearch(db, query)
        if (vectorResults.length > 0) {
          return vectorResults
        }
      } catch (error) {
      }
      
      // Fallback to enhanced text search
      const sql = `
        SELECT 
          name,
          filename,
          local_path,
          description,
          width,
          height,
          CASE 
            WHEN LOWER(name) = LOWER(?) THEN 100
            WHEN LOWER(name) LIKE LOWER(?) THEN 90
            WHEN LOWER(description) LIKE '%' || LOWER(?) || '%' THEN 80
            WHEN LOWER(name) LIKE '%' || LOWER(?) || '%' THEN 70
            ELSE 50
          END as relevance_score
        FROM icons 
        WHERE LOWER(name) LIKE '%' || LOWER(?) || '%' 
           OR LOWER(description) LIKE '%' || LOWER(?) || '%'
        ORDER BY relevance_score DESC, name
        LIMIT 200
      `
      const searchTerm = query.trim()
      const params = [searchTerm, `${searchTerm}%`, searchTerm, searchTerm, searchTerm, searchTerm]
      
      return executeQuery(db, sql, params)
    }
  } catch (error) {
    console.error('Error searching icons:', error)
    throw error
  }
}

function executeQuery(db, sql, params) {
  const stmt = db.prepare(sql)
  const results = []

  // Bind parameters if any
  if (params.length > 0) {
    stmt.bind(params)
  }

  while (stmt.step()) {
    const row = stmt.getAsObject()
    results.push({
      name: row.name,
      filename: row.filename,
      localPath: row.local_path,
      description: row.description,
      width: row.width,
      height: row.height,
      webPath: row.local_path ? row.local_path.replace(/^static\//, './') : null
    })
  }

  stmt.free()
  return results
}

async function performVectorSearch(db, query) {
  // Generate embedding for the search query
  const queryEmbedding = await generateQueryEmbedding(query)
  if (!queryEmbedding) {
    throw new Error('Failed to generate query embedding')
  }

  // Get all icons with their embeddings from database
  const stmt = db.prepare(`
    SELECT 
      name,
      filename,
      local_path,
      description,
      width,
      height,
      embedding
    FROM icons 
    WHERE embedding IS NOT NULL AND embedding != ''
  `)

  const results = []
  while (stmt.step()) {
    const row = stmt.getAsObject()
    try {
      // Parse the stored embedding
      const iconEmbedding = JSON.parse(row.embedding)
      
      // Calculate cosine similarity
      const similarity = cosineSimilarity(queryEmbedding, iconEmbedding)
      
      results.push({
        name: row.name,
        filename: row.filename,
        localPath: row.local_path,
        description: row.description,
        width: row.width,
        height: row.height,
        webPath: row.local_path ? row.local_path.replace(/^static\//, './') : null,
        similarity: similarity
      })
    } catch (e) {
      // Skip icons with invalid embeddings
      console.warn(`Invalid embedding for icon: ${row.name}`)
      continue
    }
  }

  stmt.free()

  // Sort by similarity (highest first) and return top results
  results.sort((a, b) => b.similarity - a.similarity)
  
  return results.slice(0, 50) // Return top 50 most similar for better performance
}

async function generateQueryEmbedding(query) {
  try {
    // Use the same embedding model as we used for indexing
    const { generateEmbedding } = await import('./embeddings.js')
    return await generateEmbedding(query)
  } catch (error) {
    console.error('Error generating query embedding:', error)
    return null
  }
}

function cosineSimilarity(a, b) {
  let dotProduct = 0
  let normA = 0
  let normB = 0
  
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i]
    normA += a[i] * a[i]
    normB += b[i] * b[i]
  }
  
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB))
}

export async function getIconById(db, iconName) {
  if (!db) {
    throw new Error('Database not initialized')
  }

  try {
    const stmt = db.prepare(`
      SELECT 
        name,
        filename,
        local_path,
        description,
        width,
        height
      FROM icons 
      WHERE name = ?
    `)
    
    stmt.bind([iconName])
    
    if (stmt.step()) {
      const row = stmt.getAsObject()
      stmt.free()
      
      return {
        name: row.name,
        filename: row.filename,
        localPath: row.local_path,
        description: row.description,
        width: row.width,
        height: row.height,
        webPath: row.local_path ? row.local_path.replace(/^static\//, './') : null
      }
    }
    
    stmt.free()
    return null

  } catch (error) {
    console.error('Error getting icon by ID:', error)
    throw error
  }
}