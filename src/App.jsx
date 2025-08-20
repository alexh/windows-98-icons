import React, { useState, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import {
  Window,
  WindowContent,
  WindowHeader,
  Button,
  TextInput,
  Toolbar,
  Panel,
  Separator,
  ScrollView,
  Checkbox
} from 'react95'
import IconGrid from './components/IconGrid'
import IconModal from './components/IconModal'
import { loadDatabase, searchIcons } from './services/database'
import { initializeEmbeddings } from './services/embeddings'

const AppContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  
  @media (max-height: 500px) and (orientation: landscape) {
    padding: 10px;
    min-height: 100vh;
    height: 100vh;
  }
`

const MainWindow = styled(Window)`
  width: 90vw;
  max-width: 1200px;
  height: 80vh;
  min-height: 600px;
  display: flex;
  flex-direction: column;
  
  @media (max-height: 500px) and (orientation: landscape) {
    height: 95vh;
    min-height: unset;
  }
`

const SearchContainer = styled.div`
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
  
  @media (max-width: 768px) {
    width: 100%;
    margin-bottom: 8px;
    
    span {
      display: none; /* Hide "Smart Search:" label on mobile */
    }
  }
`

const ButtonGroup = styled.div`
  display: flex;
  gap: 4px;
  align-items: center;
  flex-wrap: wrap;
  
  @media (max-width: 768px) {
    width: 100%;
    justify-content: space-between;
    
    button {
      flex: 1;
      min-width: 0;
      font-size: 11px;
      padding: 2px 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
`

const ResponsiveToolbar = styled(Toolbar)`
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: stretch;
  
  @media (min-width: 769px) {
    flex-direction: row;
    align-items: center;
  }
`

const ResponsiveTextInput = styled(TextInput)`
  width: 300px;
  
  @media (max-width: 768px) {
    width: 100%;
    flex: 1;
  }
`

const ResponsiveSeparator = styled.div`
  @media (max-width: 768px) {
    display: none;
  }
`

const AiSearchContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
  background: ${props => props.$active ? '#000080' : 'transparent'};
  color: ${props => props.$active ? 'white' : 'black'};
  border: 1px ${props => props.$active ? 'inset' : 'outset'} #c0c0c0;
`

const MagicIcon = styled.img`
  width: 16px;
  height: 16px;
  image-rendering: pixelated;
  animation: ${props => props.$searching ? 'pulse 1s infinite' : 'none'};
  
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
  }
`

const FlexWindowContent = styled(WindowContent)`
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
`

const GridContainer = styled.div`
  flex: 1;
  min-height: 0;
`

const StatsContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: ${({ theme }) => theme.canvas};
  border: ${({ theme }) => `1px inset ${theme.borderDark}`};
  font-size: 11px;
  position: relative;
  z-index: 1;
  margin: 0 -1px;
`

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  font-size: 14px;
`

function App() {
  const [db, setDb] = useState(null)
  const [icons, setIcons] = useState([])
  const [filteredIcons, setFilteredIcons] = useState([])
  const [selectedIcons, setSelectedIcons] = useState(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedIcon, setSelectedIcon] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [searchMode, setSearchMode] = useState('text') // 'text' | 'vector' | 'loading'
  const [modelLoadingState, setModelLoadingState] = useState(null)

  // Load database and icons on mount
  useEffect(() => {
    const initializeApp = async () => {
      try {
        setIsLoading(true)
        setModelLoadingState({ status: 'loading', message: 'Loading database...' })
        
        const database = await loadDatabase()
        setDb(database)
        
        // Initialize embedding model in the background
        setModelLoadingState({ status: 'loading', message: 'Loading AI model...' })
        try {
          await initializeEmbeddings((progress) => {
            setModelLoadingState(progress)
          })
        } catch (embeddingError) {
          console.warn('Embedding model failed to load, vector search disabled:', embeddingError)
          setModelLoadingState({ status: 'error', message: 'AI search unavailable, text search only' })
        }
        
        // Load all icons
        const allIcons = await searchIcons(database, '')
        setIcons(allIcons)
        setFilteredIcons(allIcons)
        setError(null)
        
        // Set final model loading state
        if (modelLoadingState?.status !== 'error') {
          setModelLoadingState({ status: 'success', message: 'Ready for AI search!' })
          setTimeout(() => setModelLoadingState(null), 3000) // Clear after 3 seconds
        }
      } catch (err) {
        console.error('Failed to initialize app:', err)
        setError('Failed to load icons database. Please check that icons.db exists in the static folder.')
      } finally {
        setIsLoading(false)
      }
    }

    initializeApp()
  }, [])


  // Search functionality with improved debouncing
  useEffect(() => {
    if (!db) return

    // Immediate search for empty query (show all icons)
    if (!searchQuery || searchQuery.trim() === '') {
      setFilteredIcons(icons)
      setSearchMode('text')
      setIsSearching(false)
      setSelectedIcons(new Set())
      return
    }

    // Show loading state immediately for responsiveness
    setIsSearching(true)
    setSearchMode('loading')

    const searchTimeout = setTimeout(async () => {
      try {
        // Smart search with vector search first, fallback to text
        const results = await searchIcons(db, searchQuery.trim())
        setFilteredIcons(results)
        
        // Determine what search mode was actually used
        if (results.length > 0 && results[0].similarity !== undefined) {
          setSearchMode('vector')
        } else {
          setSearchMode('text')  
        }
        
        // Clear selection when search changes
        setSelectedIcons(new Set())
      } catch (err) {
        console.error('Search error:', err)
        setError('Search failed')
        setSearchMode('text')
      } finally {
        setIsSearching(false)
      }
    }, 500) // Increased debounce to 500ms for better performance

    return () => clearTimeout(searchTimeout)
  }, [searchQuery, db, icons])

  const handleSearchChange = useCallback((e) => {
    setSearchQuery(e.target.value)
  }, [])

  const handleClearSearch = useCallback(() => {
    setSearchQuery('')
  }, [])

  const handleSelectAll = useCallback(() => {
    const allNames = new Set(filteredIcons.map(icon => icon.name))
    setSelectedIcons(allNames)
  }, [filteredIcons])

  const handleClearSelection = useCallback(() => {
    setSelectedIcons(new Set())
  }, [])

  const handleIconSelect = useCallback((iconName, isSelected) => {
    setSelectedIcons(prev => {
      const newSet = new Set(prev)
      if (isSelected) {
        newSet.add(iconName)
      } else {
        newSet.delete(iconName)
      }
      return newSet
    })
  }, [])

  const handleIconDoubleClick = useCallback((icon) => {
    setSelectedIcon(icon)
    setShowModal(true)
  }, [])

  const handleCloseModal = useCallback(() => {
    setShowModal(false)
    setSelectedIcon(null)
  }, [])

  const downloadIcon = useCallback(async (icon) => {
    try {
      const response = await fetch(icon.webPath)
      if (!response.ok) throw new Error('Failed to fetch icon')
      
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = icon.filename || `${icon.name}.ico`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download error:', error)
      alert('Failed to download icon')
    }
  }, [])

  const handleDownloadSelected = useCallback(async () => {
    const selectedIconData = icons.filter(icon => selectedIcons.has(icon.name))
    
    // Download each selected icon
    for (const icon of selectedIconData) {
      try {
        await downloadIcon(icon)
        // Small delay between downloads
        await new Promise(resolve => setTimeout(resolve, 100))
      } catch (error) {
        console.error(`Failed to download ${icon.name}:`, error)
      }
    }
  }, [selectedIcons, icons, downloadIcon])

  const handleDownloadSingle = useCallback(() => {
    if (selectedIcon) {
      downloadIcon(selectedIcon)
      handleCloseModal()
    }
  }, [selectedIcon, downloadIcon, handleCloseModal])

  if (isLoading) {
    return (
      <AppContainer>
        <MainWindow>
          <WindowHeader>
            <span>Windows 98 Icons - Loading...</span>
          </WindowHeader>
          <WindowContent>
            <LoadingContainer>
              Loading icons database...
            </LoadingContainer>
          </WindowContent>
        </MainWindow>
      </AppContainer>
    )
  }

  if (error) {
    return (
      <AppContainer>
        <MainWindow>
          <WindowHeader>
            <span>Windows 98 Icons - Error</span>
          </WindowHeader>
          <WindowContent>
            <Panel variant="well" style={{ padding: 20, textAlign: 'center' }}>
              <p style={{ color: 'red', marginBottom: 16 }}>{error}</p>
              <Button onClick={() => window.location.reload()}>
                Retry
              </Button>
            </Panel>
          </WindowContent>
        </MainWindow>
      </AppContainer>
    )
  }

  return (
    <AppContainer>
      <MainWindow>
        <WindowHeader>
          <img 
            src="./icons/list_of_icons_icon.png" 
            alt="List icon" 
            style={{ width: '16px', height: '16px', marginRight: '8px', imageRendering: 'pixelated' }}
          />
          <span className="desktop-title">Windows 98 Icons - Search & Download</span>
          <span className="mobile-title">Windows 98</span>
        </WindowHeader>
        <FlexWindowContent>
          <ResponsiveToolbar>
            <SearchContainer>
              <MagicIcon 
                src="./icons/internet_connection_wiz_3.png" 
                alt="AI Search"
                $searching={isSearching}
              />
              <span>Smart Search:</span>
              <ResponsiveTextInput
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Describe what you're looking for..."
              />
              <Button onClick={handleClearSearch}>
                Clear
              </Button>
            </SearchContainer>
            
            <ResponsiveSeparator>
              <Separator orientation="vertical" />
            </ResponsiveSeparator>
            
            <ButtonGroup>
              <Button onClick={handleSelectAll}>
                Select All
              </Button>
              <Button 
                onClick={handleDownloadSelected}
                disabled={selectedIcons.size === 0}
              >
                Download ({selectedIcons.size})
              </Button>
              <Button onClick={handleClearSelection}>
                Clear
              </Button>
            </ButtonGroup>
          </ResponsiveToolbar>

          <GridContainer>
            <IconGrid
              icons={filteredIcons}
              selectedIcons={selectedIcons}
              onIconSelect={handleIconSelect}
              onIconDoubleClick={handleIconDoubleClick}
            />
          </GridContainer>

          <StatsContainer>
            <span>
              {searchQuery ? (
                searchMode === 'vector' 
                  ? `AI found ${filteredIcons.length} icons for "${searchQuery}"`
                  : searchMode === 'loading'
                  ? `Searching...`
                  : `Found ${filteredIcons.length} icons for "${searchQuery}"`
              ) : `${icons.length} total icons`}
            </span>
            <span>
              {selectedIcons.size} selected
            </span>
          </StatsContainer>
        </FlexWindowContent>
      </MainWindow>

      {showModal && selectedIcon && (
        <IconModal
          icon={selectedIcon}
          onClose={handleCloseModal}
          onDownload={handleDownloadSingle}
        />
      )}
    </AppContainer>
  )
}

export default App