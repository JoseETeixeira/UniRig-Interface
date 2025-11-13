# UniRig UI - Frontend

Web-based user interface for UniRig automatic 3D model rigging.

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **Three.js** - 3D rendering
- **React Three Fiber** - React renderer for Three.js
- **React Three Drei** - Helpers for React Three Fiber
- **Axios** - HTTP client
- **react-dropzone** - File upload component

## Project Structure

```
src/
├── components/         # React components
│   ├── Upload/        # File upload UI
│   ├── Viewer/        # 3D model preview
│   ├── Jobs/          # Job queue display
│   ├── Processing/    # Processing controls
│   └── Common/        # Reusable components
├── services/          # API clients
├── hooks/             # Custom React hooks
├── types/             # TypeScript type definitions
├── utils/             # Utility functions
├── App.tsx            # Root component
├── main.tsx           # Entry point
└── index.css          # Global styles
```

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

Runs the app at http://localhost:3000

API requests to `/api/*` are automatically proxied to `http://localhost:8000`

### Build for Production

```bash
npm run build
```

Outputs to `dist/` directory

### Preview Production Build

```bash
npm run preview
```

### Linting

```bash
npm run lint
```

## Configuration

### Vite Config (`vite.config.ts`)

- Dev server runs on port 3000
- API proxy forwards `/api/*` to backend at `http://localhost:8000`

### TypeScript Config (`tsconfig.json`)

- Strict mode enabled
- ES2020 target
- React JSX transform

## Type Definitions

TypeScript interfaces in `src/types/index.ts` match the backend data models:

- `Job` - Rigging job data
- `JobStatus` - Job status enum
- `JobStage` - Processing stage enum
- `Session` - User session data
- `UploadResponse` - Upload API response
- `HealthResponse` - Health check response
- `ErrorResponse` - Error response format

## Next Steps

1. Implement API service layer (`src/services/api.ts`)
2. Create custom hooks for upload and job management
3. Build upload UI components
4. Implement 3D viewer with Three.js
5. Add job queue and progress tracking
6. Implement export functionality
