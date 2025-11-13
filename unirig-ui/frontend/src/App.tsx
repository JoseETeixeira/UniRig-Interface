import React, { useState, useEffect } from 'react';
import { ErrorBoundary, Header, Footer } from './components/Layout';
import { Modal, Button, NotificationProvider } from './components/Common';
import { SettingsView } from './components/Settings';
import { useSession } from './hooks/useSession';

type View = 'upload' | 'jobs' | 'settings';

/**
 * Main application component
 */
function App() {
  const [currentView, setCurrentView] = useState<View>('upload');
  const [isLoading, setIsLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showMobileWarning, setShowMobileWarning] = useState(false);
  const { sessionId } = useSession();

  // Initialize session on mount
  useEffect(() => {
    const init = async () => {
      // Session is automatically initialized by useSession hook
      
      // Check if this is first visit
      const hasSeenOnboarding = localStorage.getItem('unirig_onboarding_complete');
      if (!hasSeenOnboarding) {
        setShowOnboarding(true);
      }

      // Check if mobile device
      const isMobile = window.innerWidth < 768;
      if (isMobile) {
        setShowMobileWarning(true);
      }

      setIsLoading(false);
    };

    init();
  }, []); // Empty dependency array - only run once on mount

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // ESC to close modals is handled by Modal component
      // Add more global shortcuts here if needed
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case '1':
            event.preventDefault();
            setCurrentView('upload');
            break;
          case '2':
            event.preventDefault();
            setCurrentView('jobs');
            break;
          case '3':
            event.preventDefault();
            setCurrentView('settings');
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleOnboardingComplete = () => {
    localStorage.setItem('unirig_onboarding_complete', 'true');
    setShowOnboarding(false);
  };

  const handleMobileWarningClose = () => {
    setShowMobileWarning(false);
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <ErrorBoundary>
      <NotificationProvider>
        <div className="min-h-screen flex flex-col bg-gray-50">
          <Header currentView={currentView} onNavigate={setCurrentView} />

          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <ViewRenderer view={currentView} sessionId={sessionId} />
          </main>

          <Footer />

          {/* Onboarding Tutorial */}
          <OnboardingModal
            isOpen={showOnboarding}
            onClose={handleOnboardingComplete}
          />

          {/* Mobile Warning */}
          <Modal
            isOpen={showMobileWarning}
            onClose={handleMobileWarningClose}
            title="Desktop Browser Recommended"
            size="sm"
          >
            <div className="text-center">
              <div className="text-4xl mb-4">📱➡️💻</div>
              <p className="text-gray-700 mb-4">
                For the best experience with 3D model visualization and processing, we recommend using UniRig on a desktop browser.
              </p>
              <p className="text-sm text-gray-600">
                Mobile devices may have limited functionality and performance.
              </p>
            </div>
            <div className="mt-6">
              <Button variant="primary" className="w-full" onClick={handleMobileWarningClose}>
                Continue Anyway
              </Button>
            </div>
          </Modal>
        </div>
      </NotificationProvider>
    </ErrorBoundary>
  );
}

/**
 * Loading screen shown during app initialization
 */
const LoadingScreen: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="text-6xl mb-4 animate-bounce">🦴</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">UniRig</h1>
        <p className="text-gray-600 mb-4">Loading application...</p>
        <div className="flex items-center justify-center gap-2">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
        </div>
      </div>
    </div>
  );
};

/**
 * Onboarding modal for first-time users
 */
interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const OnboardingModal: React.FC<OnboardingModalProps> = ({ isOpen, onClose }) => {
  const [step, setStep] = useState(0);

  const steps = [
    {
      title: 'Welcome to UniRig! 🦴',
      content: 'UniRig automatically generates skeletons and skinning weights for your 3D models using deep learning.',
      icon: '👋',
    },
    {
      title: 'Upload Your Model 📤',
      content: 'Drag and drop your 3D model (.obj, .fbx, .glb, .vrm) to get started. The system will validate and process your file.',
      icon: '📤',
    },
    {
      title: 'Generate Skeleton 🦴',
      content: 'Click "Generate Skeleton" to predict bone structure. You can adjust the random seed and regenerate until satisfied.',
      icon: '🦴',
    },
    {
      title: 'Generate Skinning ✨',
      content: 'After approving the skeleton, generate skinning weights. Preview the rigged model with animation controls.',
      icon: '✨',
    },
    {
      title: 'Export Your Model 📦',
      content: 'Download your rigged model in FBX or GLB format. Ready to use in your game engine or animation software!',
      icon: '📦',
    },
  ];

  const currentStep = steps[step];
  const isLastStep = step === steps.length - 1;

  const handleNext = () => {
    if (isLastStep) {
      onClose();
    } else {
      setStep(step + 1);
    }
  };

  const handlePrevious = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  const handleSkip = () => {
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Getting Started" size="md">
      <div className="text-center py-4">
        <div className="text-6xl mb-4">{currentStep.icon}</div>
        <h3 className="text-xl font-bold text-gray-900 mb-3">{currentStep.title}</h3>
        <p className="text-gray-700 mb-6">{currentStep.content}</p>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-6">
          {steps.map((_, index) => (
            <div
              key={index}
              className={`h-2 rounded-full transition-all ${
                index === step ? 'w-8 bg-blue-600' : 'w-2 bg-gray-300'
              }`}
            />
          ))}
        </div>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between gap-3">
          <Button variant="ghost" onClick={handleSkip} size="sm">
            Skip Tutorial
          </Button>
          <div className="flex gap-2">
            {step > 0 && (
              <Button variant="secondary" onClick={handlePrevious}>
                Previous
              </Button>
            )}
            <Button variant="primary" onClick={handleNext}>
              {isLastStep ? 'Get Started' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

/**
 * View renderer - renders different views based on current navigation
 */
interface ViewRendererProps {
  view: View;
  sessionId: string | null;
}

const ViewRenderer: React.FC<ViewRendererProps> = ({ view, sessionId }) => {
  // Placeholder views - these will be replaced with actual components in later tasks
  switch (view) {
    case 'upload':
      return (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold mb-4">Upload View</h2>
          <p className="text-gray-600 mb-4">Session ID: {sessionId}</p>
          <p className="text-gray-600">
            Upload interface will be implemented here with drag-and-drop functionality.
          </p>
        </div>
      );
    case 'jobs':
      return (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold mb-4">Jobs View</h2>
          <p className="text-gray-600">
            Job management interface will be implemented here.
          </p>
        </div>
      );
    case 'settings':
      return <SettingsView />;
    default:
      return <div>Unknown view</div>;
  }
};

export default App
