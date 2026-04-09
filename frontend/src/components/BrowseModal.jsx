import { useState, useEffect } from 'react'
import { browseApi } from '../api/client'

function BrowseModal({ config, onSelect, onClose }) {
  const [currentPath, setCurrentPath] = useState(config.path || '/mnt/c')
  const [dirs, setDirs] = useState([])
  const [files, setFiles] = useState([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState(null)
  const [newFolderName, setNewFolderName] = useState('')

  useEffect(() => {
    fetchDirectory(currentPath)
  }, [currentPath, search])

  const fetchDirectory = async (path) => {
    try {
      const response = await browseApi.browse({
        target: config.target,
        mode: config.mode,
        path: path,
        q: search
      })
      
      // Parse HTML response
      const parser = new DOMParser()
      const doc = parser.parseFromString(response.data, 'text/html')
      
      const dirElements = doc.querySelectorAll('.dir-item')
      const fileElements = doc.querySelectorAll('.file-item')
      
      setDirs(Array.from(dirElements).map(el => el.textContent.trim()))
      setFiles(Array.from(fileElements).map(el => el.textContent.trim()))
      setError(doc.querySelector('.error')?.textContent || null)
    } catch (err) {
      setError('Failed to load directory')
      console.error(err)
    }
  }

  const handleDirClick = (dirName) => {
    const newPath = `${currentPath}/${dirName}`.replace(/\/+/g, '/')
    setCurrentPath(newPath)
  }

  const handleFileClick = (fileName) => {
    const fullPath = `${currentPath}/${fileName}`.replace(/\/+/g, '/')
    onSelect(fullPath)
  }

  const handleParentClick = () => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/'
    setCurrentPath(parentPath)
  }

  const handleSelectCurrent = () => {
    onSelect(currentPath)
  }

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return
    
    try {
      const params = new URLSearchParams({
        path: currentPath,
        name: newFolderName,
        target: config.target,
        mode: config.mode,
        q: search
      })
      
      await browseApi.mkdir(params)
      setNewFolderName('')
      fetchDirectory(currentPath)
    } catch (err) {
      setError('Failed to create folder')
      console.error(err)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold">
              Browse {config.mode === 'dir' ? 'Folder' : 'File'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            >
              ×
            </button>
          </div>
          
          {/* Current path */}
          <div className="text-sm text-gray-600 mb-3 font-mono bg-gray-50 p-2 rounded">
            {currentPath}
          </div>

          {/* Search */}
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
              {error}
            </div>
          )}

          {/* Parent directory */}
          <button
            onClick={handleParentClick}
            className="w-full text-left px-4 py-2 hover:bg-gray-100 rounded-lg mb-2 flex items-center gap-2"
          >
            <span className="text-blue-600">📁</span>
            <span className="font-semibold">..</span>
          </button>

          {/* Directories */}
          {dirs.map((dir, idx) => (
            <button
              key={`dir-${idx}`}
              onClick={() => handleDirClick(dir)}
              className="w-full text-left px-4 py-2 hover:bg-gray-100 rounded-lg mb-1 flex items-center gap-2"
            >
              <span className="text-blue-600">📁</span>
              <span>{dir}</span>
            </button>
          ))}

          {/* Files (only in file mode) */}
          {config.mode === 'file' && files.map((file, idx) => (
            <button
              key={`file-${idx}`}
              onClick={() => handleFileClick(file)}
              className="w-full text-left px-4 py-2 hover:bg-blue-50 rounded-lg mb-1 flex items-center gap-2"
            >
              <span className="text-gray-600">📄</span>
              <span>{file}</span>
            </button>
          ))}

          {dirs.length === 0 && files.length === 0 && !error && (
            <div className="text-center py-8 text-gray-400">
              No items found
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 space-y-3">
          {/* Create folder */}
          {config.mode === 'dir' && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="New folder name"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyPress={(e) => e.key === 'Enter' && handleCreateFolder()}
              />
              <button
                onClick={handleCreateFolder}
                className="px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200"
              >
                Create Folder
              </button>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            {config.mode === 'dir' && (
              <button
                onClick={handleSelectCurrent}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Select Current
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default BrowseModal
