import React from 'react'
import styled from 'styled-components'
import {
  Window,
  WindowContent,
  WindowHeader,
  Button,
  Panel
} from 'react95'

const ModalContent = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  min-width: 300px;
`

const LargeIcon = styled.img`
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
`

const IconTitle = styled.h3`
  margin: 0 0 8px 0;
  font-size: 14px;
  text-align: center;
`

const IconDescription = styled.p`
  margin: 0 0 16px 0;
  font-size: 11px;
  text-align: center;
  color: #333;
  line-height: 1.4;
  max-width: 250px;
`

const IconDetails = styled.div`
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 16px;
  margin-bottom: 16px;
  font-size: 11px;
  width: 100%;
  max-width: 250px;
`

const DetailLabel = styled.span`
  font-weight: bold;
  color: #333;
`

const DetailValue = styled.span`
  color: #666;
`

const ButtonContainer = styled.div`
  display: flex;
  gap: 8px;
  justify-content: center;
`

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`

const ModalWindow = styled(Window)`
  width: 400px;
  max-width: 90vw;
`

const IconModal = ({ icon, onClose, onDownload }) => {
  if (!icon) return null

  return (
    <ModalOverlay onClick={onClose}>
      <ModalWindow onClick={(e) => e.stopPropagation()}>
        <WindowHeader>
          <span>Icon Details</span>
          <Button onClick={onClose} size="sm" style={{ marginLeft: 'auto' }}>
            ×
          </Button>
        </WindowHeader>
        <WindowContent>
          <ModalContent>
            <LargeIcon
              src={icon.webPath || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjQzBDMEMwIi8+CjwvZz4K'}
              alt={icon.name}
              onError={(e) => {
                e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjQzBDMEMwIi8+CjwvZz4K'
              }}
            />
            
            <IconTitle>
              {icon.name.replace(/_/g, ' ')}
            </IconTitle>
            
            <IconDescription>
              {icon.description}
            </IconDescription>
            
            <Panel variant="well" style={{ width: '100%', marginBottom: 16 }}>
              <IconDetails>
                <DetailLabel>Filename:</DetailLabel>
                <DetailValue>{icon.filename || 'N/A'}</DetailValue>
                
                <DetailLabel>Dimensions:</DetailLabel>
                <DetailValue>
                  {icon.width && icon.height ? `${icon.width} × ${icon.height}` : 'Unknown'}
                </DetailValue>
                
                <DetailLabel>Name:</DetailLabel>
                <DetailValue>{icon.name}</DetailValue>
              </IconDetails>
            </Panel>
            
            <ButtonContainer>
              <Button onClick={onDownload}>
                Download
              </Button>
              <Button onClick={onClose}>
                Cancel
              </Button>
            </ButtonContainer>
          </ModalContent>
        </WindowContent>
      </ModalWindow>
    </ModalOverlay>
  )
}

export default IconModal