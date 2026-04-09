# GS Platform Frontend

React + Tailwind CSS frontend for the Gaussian Splatting Platform.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will run on http://localhost:3000 and proxy API requests to the Python backend at http://localhost:8000.

## Build for Production

```bash
npm run build
```

The production build will be in the `dist` directory.

## Features

- Job creation form with file browser
- Real-time job list updates
- Job detail page with live log streaming
- Responsive design with Tailwind CSS
- API integration with FastAPI backend
