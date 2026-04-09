import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export const Upload: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = droppedFiles.filter(file => 
      file.type.startsWith('image/') || file.type.startsWith('video/')
    );
    
    if (validFiles.length === 0) {
      setError('Please drop valid image or video files');
      return;
    }
    
    setFiles(validFiles);
    setError(null);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(selectedFiles);
      setError(null);
    }
  }, []);

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select files to upload');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          setProgress({
            loaded: e.loaded,
            total: e.total,
            percentage: Math.round((e.loaded / e.total) * 100)
          });
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          const jobId = response.job_id;
          navigate(`/processing/${jobId}`);
        } else {
          setError(`Upload failed: ${xhr.statusText}`);
          setUploading(false);
        }
      });

      xhr.addEventListener('error', () => {
        setError('Upload failed due to network error');
        setUploading(false);
      });

      xhr.open('POST', '/api/upload');
      xhr.send(formData);
    } catch (err) {
      setError(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Upload Images or Video</h1>

        <div
          className={`border-4 border-dashed rounded-lg p-12 text-center transition-colors ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="mb-4">
            <svg
              className="mx-auto h-16 w-16 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          <p className="text-lg mb-2">Drag and drop files here</p>
          <p className="text-gray-500 mb-4">or</p>
          <label className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700">
            Browse Files
            <input
              type="file"
              multiple
              accept="image/*,video/*"
              className="hidden"
              onChange={handleFileSelect}
              disabled={uploading}
            />
          </label>
        </div>

        {files.length > 0 && (
          <div className="mt-6 bg-white rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Selected Files ({files.length})</h2>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {files.map((file, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="truncate flex-1">{file.name}</span>
                  <span className="text-gray-500 ml-4">{formatFileSize(file.size)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {progress && (
          <div className="mt-6 bg-white rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Uploading...</h2>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
            <p className="text-center mt-2 text-gray-600">
              {progress.percentage}% ({formatFileSize(progress.loaded)} / {formatFileSize(progress.total)})
            </p>
          </div>
        )}

        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {files.length > 0 && !uploading && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleUpload}
              className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
            >
              Start Reconstruction
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
