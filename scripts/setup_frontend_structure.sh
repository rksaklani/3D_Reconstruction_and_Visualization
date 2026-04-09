#!/bin/bash
# Setup Frontend Structure - Public Website + Dashboard App

echo "Setting up frontend structure..."

cd frontend/src

# Create directory structure
mkdir -p layouts
mkdir -p pages/public
mkdir -p pages/dashboard
mkdir -p components/public
mkdir -p components/dashboard
mkdir -p context
mkdir -p hooks
mkdir -p utils

echo "✓ Directory structure created"

# Create placeholder files
touch layouts/PublicLayout.jsx
touch layouts/DashboardLayout.jsx

# Public pages
touch pages/public/Home.jsx
touch pages/public/Features.jsx
touch pages/public/Pricing.jsx
touch pages/public/About.jsx
touch pages/public/Contact.jsx
touch pages/public/Login.jsx
touch pages/public/Signup.jsx

# Dashboard pages
touch pages/dashboard/Dashboard.jsx
touch pages/dashboard/Projects.jsx
touch pages/dashboard/ProjectDetail.jsx
touch pages/dashboard/AIAnalysis.jsx
touch pages/dashboard/Models.jsx
touch pages/dashboard/Exports.jsx
touch pages/dashboard/Storage.jsx
touch pages/dashboard/Team.jsx
touch pages/dashboard/Analytics.jsx
touch pages/dashboard/Settings.jsx
touch pages/dashboard/Help.jsx

# Public components
touch components/public/Hero.jsx
touch components/public/FeatureCard.jsx
touch components/public/PricingCard.jsx
touch components/public/DemoViewer.jsx
touch components/public/PublicHeader.jsx
touch components/public/PublicFooter.jsx

# Dashboard components
touch components/dashboard/Sidebar.jsx
touch components/dashboard/Topbar.jsx
touch components/dashboard/ProjectCard.jsx
touch components/dashboard/UploadZone.jsx
touch components/dashboard/ProgressBar.jsx
touch components/dashboard/StatusBadge.jsx
touch components/dashboard/Viewer3D.jsx

# Context
touch context/AuthContext.jsx
touch context/ThemeContext.jsx

# Hooks
touch hooks/useAuth.js
touch hooks/useProjects.js

# Utils
touch utils/auth.js
touch utils/format.js
touch utils/constants.js

echo "✓ All files created"
echo ""
echo "Frontend structure ready!"
echo "Next: Implement components in frontend/src/"
