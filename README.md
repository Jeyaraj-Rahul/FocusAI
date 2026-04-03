# FocusAI: AI Distraction Detection System

FocusAI is a full-stack web application that monitors user focus using computer vision and browser activity signals.

It uses a Flask backend, an HTML/CSS/JavaScript frontend, and OpenCV-based webcam processing to estimate whether the user is focused or distracted.

## Features

- Face detection using webcam
- Focus score from 0 to 100
- Focus state detection:
  - Deep Focus
  - Mild Distraction
  - High Distraction
- Browser tab switch tracking
- Website usage tracking
- Session summary tracking
- Live dashboard with:
  - focus score
  - current state
  - camera preview
  - focus trend graph
  - website usage panel
  - session summary panel
- Optional sound alert
- OpenCV fallback mode if MediaPipe is unavailable

## Tech Stack

- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Computer Vision: OpenCV
- Face Landmark Detection: MediaPipe Face Mesh
- Charts: Chart.js

## Project Structure

```bash
FocusAI/
│
├── app.py
├── camera.py
├── usage_tracker.py
├── windows_control.py
├── requirements.txt
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js
