import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { jobsApi } from '../api/client'
import BrowseModal from './BrowseModal'
import Tooltip from './Tooltip'

function JobForm() {
  const navigate = useNavigate()
  const [showModal, setShowModal] = useState(false)
  const [modalConfig, setModalConfig] = useState({})
  const [formData, setFormData] = useState({
    workspace: '/mnt/c/gs_data/projects/bultt',
    gs_repo: '/home/aditya/gaussian-splatting',
    video: '',
    images_dir: '',
    fps: '2',
    jpg_quality: '2',
    matcher: 'sequential',
    overlap: '20',
    loop_detection: false,
    vocab_tree: '',
    camera_model: 'SIMPLE_RADIAL',
    single_camera: true,
    use_gpu: true,
    iterations: '30000',
    save_iters: '7000 10000 15000 20000 30000',
    checkpoint_iters: '10000 30000 40000 50000 60000',
    extra_train_args: '',
    resume: false,
  })

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const openBrowse = (target, mode, path) => {
    setModalConfig({ target, mode, path })
    setShowModal(true)
  }

  const handleSelectPath = (path) => {
    setFormData(prev => ({
      ...prev,
      [modalConfig.target]: path,
      // Clear the opposite field for video/images_dir
      ...(modalConfig.target === 'video' ? { images_dir: '' } : {}),
      ...(modalConfig.target === 'images_dir' ? { video: '' } : {}),
    }))
    setShowModal(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      const params = new URLSearchParams()
      Object.entries(formData).forEach(([key, value]) => {
        if (typeof value === 'boolean') {
          if (value) params.append(key, 'on')
        } else {
          params.append(key, value)
        }
      })

      const response = await jobsApi.createJob(params)
      // Extract job ID from redirect URL
      const jobId = response.request.responseURL.split('/').pop()
      navigate(`/job/${jobId}`)
    } catch (error) {
      console.error('Failed to create job:', error)
      alert('Failed to create job: ' + (error.response?.data?.detail || error.message))
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <div className="font-bold mb-2">Recommended defaults (object videos)</div>
          <div className="text-sm text-gray-600 leading-relaxed">
            <b>Phone / handheld / turntable object</b>: use <code className="bg-gray-200 px-2 py-0.5 rounded">SIMPLE_RADIAL</code>, 
            <b> Single camera</b> ON, <code className="bg-gray-200 px-2 py-0.5 rounded">matcher=sequential</code>, 
            <code className="bg-gray-200 px-2 py-0.5 rounded">overlap=20–40</code>.
            Enable <b>Loop detection</b> if you walk around / circle the object.
          </div>
        </div>

        {/* Workspace */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-semibold">Workspace</label>
            <Tooltip text="Project folder containing images/ colmap/ undistorted/ gs_out/ runs/" />
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              name="workspace"
              value={formData.workspace}
              onChange={handleChange}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => openBrowse('workspace', 'dir', '/mnt/c/gs_data/projects')}
              className="px-4 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
            >
              Browse
            </button>
          </div>
        </div>

        {/* GS Repo */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-semibold">GS repo</label>
            <Tooltip text="Your gaussian-splatting repo that contains train.py" />
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              name="gs_repo"
              value={formData.gs_repo}
              onChange={handleChange}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => openBrowse('gs_repo', 'dir', '/home')}
              className="px-4 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
            >
              Browse
            </button>
          </div>
        </div>

        {/* Video */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-semibold">Video path (WSL)</label>
            <Tooltip text="When choosing Video, the file browser shows only video formats. Selecting a video will automatically clear Images dir." />
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              name="video"
              value={formData.video}
              onChange={handleChange}
              placeholder="/mnt/c/Users/.../A001.mp4"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => openBrowse('video', 'file', '/mnt/c/Users')}
              className="px-4 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
            >
              Browse
            </button>
            <button
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, video: '' }))}
              className="px-4 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
            >
              Clear
            </button>
          </div>
          <div className="text-xs text-gray-500 mt-1">Use either Video OR Images dir (not both).</div>
        </div>

        {/* Images dir */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-semibold">OR Images dir (WSL)</label>
            <Tooltip text="Use this only if you already extracted frames. Selecting an images folder will automatically clear Video." />
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              name="images_dir"
              value={formData.images_dir}
              onChange={handleChange}
              placeholder="/mnt/c/gs_data/projects/bultt/images"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => openBrowse('images_dir', 'dir', '/mnt/c/gs_data/projects')}
              className="px-4 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
            >
              Browse
            </button>
            <button
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, images_dir: '' }))}
              className="px-4 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
            >
              Clear
            </button>
          </div>
        </div>

        {/* FPS and JPG Quality */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="font-semibold">FPS</label>
              <Tooltip text="Frames extracted per second from the video. Higher = more images + slower COLMAP." />
            </div>
            <input
              type="text"
              name="fps"
              value={formData.fps}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="font-semibold">JPG quality (1 best)</label>
              <Tooltip text="FFmpeg -q:v value. 1 = best quality (bigger files), 2–5 usually fine." />
            </div>
            <input
              type="text"
              name="jpg_quality"
              value={formData.jpg_quality}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Matcher */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-semibold">Matcher</label>
            <Tooltip text="sequential: best for video (fast). exhaustive: slow but robust. vocab: helps loop closure when circling object." />
          </div>
          <select
            name="matcher"
            value={formData.matcher}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="sequential">sequential (video)</option>
            <option value="exhaustive">exhaustive (slow)</option>
            <option value="vocab">vocab (loop closure)</option>
          </select>
        </div>

        {/* Overlap and Loop Detection */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="font-semibold mb-2 block">Overlap</label>
            <input
              type="text"
              name="overlap"
              value={formData.overlap}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="font-semibold mb-2 block">Loop detection</label>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                name="loop_detection"
                checked={formData.loop_detection}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <span className="text-sm text-gray-600">Enable if you circle the object</span>
            </div>
          </div>
        </div>

        {/* Vocab tree */}
        <div>
          <label className="font-semibold mb-2 block">Vocab tree path (optional)</label>
          <div className="flex gap-2">
            <input
              type="text"
              name="vocab_tree"
              value={formData.vocab_tree}
              onChange={handleChange}
              placeholder="/path/to/vocab_tree.bin"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => openBrowse('vocab_tree', 'file', '/mnt/c')}
              className="px-4 py-2 border border-gray-800 rounded-lg hover:bg-gray-50"
            >
              Browse
            </button>
          </div>
        </div>

        {/* Camera model */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-semibold">Camera model</label>
            <Tooltip text="SIMPLE_RADIAL is the best default for phone videos (handles radial distortion). PINHOLE assumes no distortion." />
          </div>
          <select
            name="camera_model"
            value={formData.camera_model}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="SIMPLE_RADIAL">SIMPLE_RADIAL (recommended)</option>
            <option value="PINHOLE">PINHOLE</option>
            <option value="OPENCV">OPENCV</option>
            <option value="RADIAL">RADIAL</option>
          </select>
        </div>

        {/* Single camera and Use GPU */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="font-semibold mb-2 block">Single camera</label>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                name="single_camera"
                checked={formData.single_camera}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <span className="text-sm text-gray-600">One intrinsics set</span>
            </div>
          </div>
          <div>
            <label className="font-semibold mb-2 block">Use GPU</label>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                name="use_gpu"
                checked={formData.use_gpu}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <span className="text-sm text-gray-600">SIFT + matching</span>
            </div>
          </div>
        </div>

        {/* Iterations and Resume */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="font-semibold mb-2 block">Iterations</label>
            <input
              type="text"
              name="iterations"
              value={formData.iterations}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="font-semibold mb-2 block">Resume</label>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                name="resume"
                checked={formData.resume}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <span className="text-sm text-gray-600">From latest checkpoint</span>
            </div>
          </div>
        </div>

        {/* Save iters */}
        <div>
          <label className="font-semibold mb-2 block">Save iters (space-separated)</label>
          <input
            type="text"
            name="save_iters"
            value={formData.save_iters}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Checkpoint iters */}
        <div>
          <label className="font-semibold mb-2 block">Checkpoint iters (space-separated)</label>
          <input
            type="text"
            name="checkpoint_iters"
            value={formData.checkpoint_iters}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Extra train args */}
        <div>
          <label className="font-semibold mb-2 block">Extra train args (optional)</label>
          <textarea
            name="extra_train_args"
            value={formData.extra_train_args}
            onChange={handleChange}
            placeholder="--resolution 1 --densification_interval 100"
            rows="3"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          type="submit"
          className="w-full px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition"
        >
          Run
        </button>
      </form>

      {showModal && (
        <BrowseModal
          config={modalConfig}
          onSelect={handleSelectPath}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  )
}

export default JobForm
