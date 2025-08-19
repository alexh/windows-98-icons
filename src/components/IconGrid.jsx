import React, { memo, useMemo, useRef, useEffect, useState } from 'react'
import styled from 'styled-components'
import { Panel } from 'react95'
import { FixedSizeGrid as Grid } from 'react-window'

const GridContainer = styled.div`
  width: 100%;
  height: 400px;
  background: white;
  border: 2px inset #c0c0c0;
`

const IconItem = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  background: ${props => props.$selected ? '#0000ff' : 'white'};
  color: ${props => props.$selected ? 'white' : 'black'};
  
  &:hover {
    background: ${props => props.$selected ? '#0000ff' : '#e0e0e0'};
  }
  
  &:active {
    background: #0000ff;
    color: white;
  }
`

const IconImage = styled.img`
  width: 32px;
  height: 32px;
  margin-bottom: 4px;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
`

const IconName = styled.div`
  font-size: 10px;
  text-align: center;
  word-break: break-word;
  line-height: 1.2;
  max-width: 80px;
`

const NoResultsContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #666;
  font-size: 14px;
`

const IconCell = memo(({ columnIndex, rowIndex, style, data }) => {
  const { icons, selectedIcons, onIconSelect, onIconDoubleClick, columnsPerRow } = data
  const iconIndex = rowIndex * columnsPerRow + columnIndex
  
  if (iconIndex >= icons.length) {
    return <div style={style} />
  }
  
  const icon = icons[iconIndex]
  
  const handleIconClick = (event) => {
    event.preventDefault()
    const isCurrentlySelected = selectedIcons.has(icon.name)
    
    if (event.ctrlKey || event.metaKey) {
      onIconSelect(icon.name, !isCurrentlySelected)
    } else {
      onIconSelect(icon.name, !isCurrentlySelected)
    }
  }

  const handleIconDoubleClick = (event) => {
    event.preventDefault()
    onIconDoubleClick(icon)
  }

  return (
    <div style={style}>
      <IconItem
        $selected={selectedIcons.has(icon.name)}
        onClick={handleIconClick}
        onDoubleClick={handleIconDoubleClick}
        title={`${icon.name}\n${icon.description}`}
        style={{ margin: '4px', height: 'calc(100% - 8px)' }}
      >
        <IconImage
          src={icon.webPath || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjQzBDMEMwIi8+CjwvZz4K'}
          alt={icon.name}
          onError={(e) => {
            e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjQzBDMEMwIi8+CjwvZz4K'
          }}
        />
        <IconName>
          {icon.name.replace(/_/g, ' ')}
        </IconName>
      </IconItem>
    </div>
  )
})

IconCell.displayName = 'IconCell'

const IconGrid = memo(({ icons, selectedIcons, onIconSelect, onIconDoubleClick }) => {
  const containerRef = useRef(null)
  const [containerWidth, setContainerWidth] = useState(800)
  
  // Update container width on resize
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth)
      }
    }
    
    updateWidth()
    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [])

  const { columnsPerRow, rowCount, itemData } = useMemo(() => {
    const itemWidth = 108 // 100px + 8px margin
    const cols = Math.max(1, Math.floor(containerWidth / itemWidth))
    const rows = Math.ceil(icons.length / cols)
    
    return {
      columnsPerRow: cols,
      rowCount: rows,
      itemData: {
        icons,
        selectedIcons,
        onIconSelect,
        onIconDoubleClick,
        columnsPerRow: cols
      }
    }
  }, [icons, selectedIcons, onIconSelect, onIconDoubleClick, containerWidth])

  if (!icons || icons.length === 0) {
    return (
      <GridContainer ref={containerRef}>
        <NoResultsContainer>
          No icons found. Try a different search term.
        </NoResultsContainer>
      </GridContainer>
    )
  }

  return (
    <GridContainer ref={containerRef}>
      <Grid
        columnCount={columnsPerRow}
        columnWidth={108}
        rowCount={rowCount}
        rowHeight={100}
        height={400}
        width={containerWidth}
        itemData={itemData}
      >
        {IconCell}
      </Grid>
    </GridContainer>
  )
})

IconGrid.displayName = 'IconGrid'

export default IconGrid