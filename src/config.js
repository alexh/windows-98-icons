// Configuration for embedding model
// This should match the EMBEDDING_MODEL environment variable used in Python scripts

export const EMBEDDING_MODEL = import.meta.env.VITE_EMBEDDING_MODEL || 'Xenova/bge-base-en-v1.5'

