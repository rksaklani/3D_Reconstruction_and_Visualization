import { useState } from 'react'

function Tooltip({ text }) {
  const [show, setShow] = useState(false)

  return (
    <div className="relative inline-flex">
      <button
        type="button"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        className="w-5 h-5 flex items-center justify-center border border-gray-800 rounded-full text-xs hover:bg-gray-100"
      >
        i
      </button>
      {show && (
        <div className="absolute z-50 top-6 right-0 w-80 bg-gray-900 text-white text-xs p-3 rounded-lg shadow-xl">
          {text}
        </div>
      )}
    </div>
  )
}

export default Tooltip
