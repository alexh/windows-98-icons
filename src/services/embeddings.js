import { pipeline, env } from '@xenova/transformers'
import { EMBEDDING_MODEL } from '../config.js'

// Configure transformers.js environment
env.allowRemoteModels = true
env.allowLocalModels = false

let embeddingPipeline = null
let isLoading = false
let loadingCallbacks = []

export async function initializeEmbeddings(onProgress = null) {
  if (embeddingPipeline) return embeddingPipeline
  if (isLoading) {
    // If already loading, add to callbacks and wait
    if (onProgress) {
      loadingCallbacks.push(onProgress)
    }
    return new Promise((resolve) => {
      const checkLoaded = () => {
        if (embeddingPipeline) {
          resolve(embeddingPipeline)
        } else if (!isLoading) {
          resolve(null)
        } else {
          setTimeout(checkLoaded, 100)
        }
      }
      checkLoaded()
    })
  }
  
  try {
    isLoading = true
    if (onProgress) loadingCallbacks.push(onProgress)
    
    // Notify all callbacks about start
    loadingCallbacks.forEach(cb => cb({ status: 'loading', message: 'Initializing embedding model...' }))
    
    // Use configured embedding model
    embeddingPipeline = await pipeline(
      'feature-extraction',
      EMBEDDING_MODEL,
      {
        quantized: true, // Use quantized version for faster loading
        progress_callback: (progress) => {
          const message = progress.status === 'downloading' 
            ? `Downloading model: ${Math.round((progress.loaded || 0) / (progress.total || 1) * 100)}%`
            : `Loading model: ${progress.status}`
          loadingCallbacks.forEach(cb => cb({ 
            status: 'loading', 
            message,
            progress: (progress.loaded || 0) / (progress.total || 1)
          }))
        }
      }
    )
    
    // Notify success
    loadingCallbacks.forEach(cb => cb({ status: 'success', message: 'Embedding model loaded successfully!' }))
    return embeddingPipeline
  } catch (error) {
    // Notify error
    loadingCallbacks.forEach(cb => cb({ status: 'error', message: `Failed to load model: ${error.message}` }))
    console.error('Failed to load embedding model:', error)
    throw error
  } finally {
    isLoading = false
    loadingCallbacks = []
  }
}

export async function generateEmbedding(text) {
  if (!embeddingPipeline) {
    await initializeEmbeddings()
  }
  
  try {
    const output = await embeddingPipeline(text, {
      pooling: 'mean',
      normalize: true
    })
    
    // Convert tensor to array
    return Array.from(output.data)
  } catch (error) {
    console.error('Error generating embedding:', error)
    throw error
  }
}

export function cosineSimilarity(a, b) {
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