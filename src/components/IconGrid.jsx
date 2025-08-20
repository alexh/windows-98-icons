import React, { memo, useMemo } from 'react'
import styled from 'styled-components'
import { Panel } from 'react95'
import { FixedSizeGrid as Grid } from 'react-window'
import AutoSizer from 'react-virtualized-auto-sizer'

const GridContainer = styled.div`
  width: 100%;
  height: 100%;
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
  const { columnsPerRow, rowCount, itemData } = useMemo(() => {
    const itemWidth = 108 // 100px + 8px margin
    
    return {
      columnsPerRow: 0, // Will be calculated in AutoSizer
      rowCount: 0, // Will be calculated in AutoSizer
      itemData: {
        icons,
        selectedIcons,
        onIconSelect,
        onIconDoubleClick,
        itemWidth
      }
    }
  }, [icons, selectedIcons, onIconSelect, onIconDoubleClick])

  if (!icons || icons.length === 0) {
    return (
      <GridContainer>
        <NoResultsContainer>
          No icons found. Try a different search term.
        </NoResultsContainer>
      </GridContainer>
    )
  }

  return (
    <GridContainer>
      <AutoSizer>
        {({ height, width }) => {
          const itemWidth = 108
          const cols = Math.max(1, Math.floor(width / itemWidth))
          const rows = Math.ceil(icons.length / cols)
          const gridWidth = cols * itemWidth
          const leftPadding = (width - gridWidth) / 2
          
          const finalItemData = {
            ...itemData,
            columnsPerRow: cols
          }
          
          return (
            <div style={{ paddingLeft: leftPadding }}>
              <Grid
                columnCount={cols}
                columnWidth={itemWidth}
                rowCount={rows}
                rowHeight={100}
                height={height}
                width={gridWidth}
                itemData={finalItemData}
              >
                {IconCell}
              </Grid>
            </div>
          )
        }}
      </AutoSizer>
    </GridContainer>
  )
})

IconGrid.displayName = 'IconGrid'

export default IconGrid