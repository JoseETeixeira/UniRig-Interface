/**
 * AnimationPanel component for displaying and selecting animations
 * Shows list of available animations with metadata (name, duration, frame count)
 * Includes motion retargeting UI for applying motion clips from dataset
 */

import { useState, useEffect, useCallback } from 'react';
import type { Animation, MotionClip } from '../../types';
import { PlaybackControls } from './PlaybackControls';
import { Modal } from '../Common/Modal';
import { MotionClipsBrowser } from '../MotionClips';
import { requestMotionRetargeting, getRetargetingJobStatus, saveRetargetedAnimation } from '../../services/api';

interface AnimationPanelProps {
  jobId?: string; // Job ID for retargeting
  animations: Animation[];
  selectedAnimationId?: string;
  onAnimationSelect?: (animationId: string) => void;
  onRetargetingComplete?: (resultPath: string, motionName: string, retargetingJobId: string) => void;
  onAnimationSaved?: (animationId: string) => void; // Callback when animation is saved
  // Playback control props
  isPlaying?: boolean;
  currentTime?: number;
  onPlay?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  onSeek?: (time: number) => void;
  playbackSpeed?: number;
  onSpeedChange?: (speed: number) => void;
  isLooping?: boolean;
  onLoopToggle?: (loop: boolean) => void;
}

/**
 * Format duration in seconds to MM:SS format
 */
function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Get retargeting phase based on progress percentage
 * Phases align with backend task implementation in retargeting_task.py
 */
function getRetargetingPhase(progress: number): string {
  if (progress < 20) return 'Preparing';
  if (progress < 40) return 'Loading Motion';
  if (progress < 50) return 'Loading Skeleton';
  if (progress < 90) return 'Retargeting Animation';
  return 'Finalizing';
}

/**
 * AnimationPanel displays a list of animations with selection capability
 * Designed for integration with ModelViewer
 * Includes motion retargeting functionality when jobId is provided
 */
export const AnimationPanel: React.FC<AnimationPanelProps> = ({
  jobId,
  animations,
  selectedAnimationId,
  onAnimationSelect,
  onRetargetingComplete,
  onAnimationSaved,
  isPlaying = false,
  currentTime = 0,
  onPlay,
  onPause,
  onStop,
  onSeek,
  playbackSpeed = 1.0,
  onSpeedChange,
  isLooping = true,
  onLoopToggle,
}) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  
  // Retargeting UI state
  const [showRetargetModal, setShowRetargetModal] = useState(false);
  const [selectedMotionClip, setSelectedMotionClip] = useState<MotionClip | null>(null);
  const [isRetargeting, setIsRetargeting] = useState(false);
  const [retargetingProgress, setRetargetingProgress] = useState(0);
  const [retargetingError, setRetargetingError] = useState<string | null>(null);
  const [currentRetargetingJobId, setCurrentRetargetingJobId] = useState<string | null>(null);
  const [showSuccessNotification, setShowSuccessNotification] = useState(false);
  const [completedMotionName, setCompletedMotionName] = useState<string>('');
  
  // Save animation state
  const [savingAnimationId, setSavingAnimationId] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  
  // Skeleton compatibility error state
  const [compatibilityError, setCompatibilityError] = useState<{
    message: string;
    compatibility: {
      compatible: boolean;
      compatibilityScore: number;
      missingBones: string[];
      extraBones: string[];
      matchedBones: string[];
      skeletonTypeMatch: boolean;
      sourceType: string;
      targetType: string;
    };
    suggestions: string[];
  } | null>(null);

  // Get selected animation for playback controls
  const selectedAnimation = animations.find(anim => anim.id === selectedAnimationId);

  // Polling for retargeting status
  useEffect(() => {
    if (!currentRetargetingJobId || !isRetargeting) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await getRetargetingJobStatus(currentRetargetingJobId);
        
        setRetargetingProgress(status.progress);

        if (status.status === 'completed') {
          setIsRetargeting(false);
          setCurrentRetargetingJobId(null);
          setRetargetingProgress(0);
          setShowRetargetModal(false);
          
          // Show success notification
          const completedName = selectedMotionClip?.name || 'Motion';
          setCompletedMotionName(completedName);
          setShowSuccessNotification(true);
          
          // Auto-hide notification after 5 seconds
          setTimeout(() => {
            setShowSuccessNotification(false);
          }, 5000);
          
          // Call completion callback to load retargeted animation
          if (onRetargetingComplete && status.resultPath) {
            onRetargetingComplete(status.resultPath, completedName, status.id);
          }
          
          setSelectedMotionClip(null);
          
          // Removed TODO: Now implemented via callback
          console.log('Retargeting completed:', status.resultPath);
          
        } else if (status.status === 'failed') {
          setIsRetargeting(false);
          setCurrentRetargetingJobId(null);
          setRetargetingProgress(0);
          setRetargetingError(status.error || 'Retargeting failed');
        }
      } catch (error) {
        console.error('Failed to poll retargeting status:', error);
        setRetargetingError('Failed to check retargeting status');
        setIsRetargeting(false);
        setCurrentRetargetingJobId(null);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(pollInterval);
  }, [currentRetargetingJobId, isRetargeting, selectedMotionClip, onRetargetingComplete]);

  const handleOpenRetargetModal = useCallback(() => {
    setShowRetargetModal(true);
    setRetargetingError(null);
    setSelectedMotionClip(null);
  }, []);

  const handleCloseRetargetModal = useCallback(() => {
    if (!isRetargeting) {
      setShowRetargetModal(false);
      setSelectedMotionClip(null);
      setRetargetingError(null);
    }
  }, [isRetargeting]);

  const handleSelectMotionClip = useCallback((clip: MotionClip) => {
    setSelectedMotionClip(clip);
    setRetargetingError(null);
  }, []);

  const handleApplyRetargeting = useCallback(async () => {
    if (!jobId || !selectedMotionClip) return;

    setIsRetargeting(true);
    setRetargetingProgress(0);
    setRetargetingError(null);
    setCompatibilityError(null);

    try {
      const response = await requestMotionRetargeting(jobId, selectedMotionClip.id);
      setCurrentRetargetingJobId(response.retargetingJobId);
    } catch (error: any) {
      console.error('Failed to request retargeting:', error);
      
      // Check if this is a skeleton incompatibility error (422 status)
      if (error.response?.status === 422 && error.response?.data?.detail?.compatibility) {
        const detail = error.response.data.detail;
        setCompatibilityError({
          message: detail.message || 'Skeleton structures are incompatible',
          compatibility: detail.compatibility,
          suggestions: detail.suggestions || []
        });
        setShowRetargetModal(false); // Close selection modal to show error
      } else {
        // Generic error handling
        setRetargetingError(
          error.response?.data?.detail?.message || 
          error.message || 
          'Failed to start retargeting. Please try again.'
        );
      }
      setIsRetargeting(false);
    }
  }, [jobId, selectedMotionClip]);

  /**
   * Handle saving a retargeted animation to the model file
   */
  const handleSaveAnimation = useCallback(async (animation: Animation) => {
    if (!jobId || !animation.retargetingJobId) return;

    setSavingAnimationId(animation.id);
    setSaveError(null);
    setSaveSuccess(null);

    try {
      await saveRetargetedAnimation(
        jobId,
        animation.retargetingJobId,
        animation.name
      );
      
      // Show success notification
      setSaveSuccess(`${animation.name} saved successfully!`);
      
      // Notify parent component to update animation source
      onAnimationSaved?.(animation.id);
      
      // Auto-hide success message after 5 seconds
      setTimeout(() => {
        setSaveSuccess(null);
      }, 5000);
      
    } catch (error: any) {
      console.error('Failed to save animation:', error);
      setSaveError(
        error.response?.data?.detail || 
        error.message || 
        'Failed to save animation. Please try again.'
      );
    } finally {
      setSavingAnimationId(null);
    }
  }, [jobId, onAnimationSaved]);

  // Handle no animations
  if (animations.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 text-center">
        <div className="text-gray-400 text-sm">
          <svg
            className="w-12 h-12 mx-auto mb-2 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="font-medium">No Animations</p>
          <p className="text-xs mt-1">This model doesn't contain any animations</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-200 flex items-center">
            <svg
              className="w-4 h-4 mr-2 text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Animations
            <span className="ml-2 px-2 py-0.5 text-xs bg-blue-600 text-white rounded-full">
              {animations.length}
            </span>
          </h3>

          {/* Retarget Animation Button - only show if jobId is provided */}
          {jobId && (
            <button
              onClick={handleOpenRetargetModal}
              disabled={isRetargeting}
              className={`
                px-3 py-1.5 text-xs font-medium rounded transition-colors
                flex items-center space-x-1
                ${isRetargeting 
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                  : 'bg-purple-600 text-white hover:bg-purple-700'
                }
              `}
              title="Retarget motion from dataset"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
              </svg>
              <span>Retarget Motion</span>
            </button>
          )}
        </div>

        {/* Retargeting Progress */}
        {isRetargeting && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-300 font-medium">
                {getRetargetingPhase(retargetingProgress)}
              </span>
              <span className="text-purple-300">{retargetingProgress}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-purple-500 to-purple-400 h-2.5 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${retargetingProgress}%` }}
              />
            </div>
            {selectedMotionClip && (
              <p className="text-xs text-gray-400 mt-2 flex items-center">
                <svg className="w-3 h-3 mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Applying "{selectedMotionClip.name}" to your rigged model
              </p>
            )}
          </div>
        )}

        {/* Retargeting Error */}
        {retargetingError && (
          <div className="mt-3 p-2 bg-red-900/50 border border-red-700 rounded text-xs text-red-200">
            {retargetingError}
          </div>
        )}
      </div>

      {/* Animation List */}
      <div className="max-h-64 overflow-y-auto">
        {animations.map((animation) => {
          const isSelected = animation.id === selectedAnimationId;
          const isHovered = animation.id === hoveredId;
          const isSaving = savingAnimationId === animation.id;
          const isRetargeted = animation.source === 'retargeted';

          return (
            <div key={animation.id} className="relative">
              <button
                onClick={() => onAnimationSelect?.(animation.id)}
                onMouseEnter={() => setHoveredId(animation.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`
                  w-full px-4 py-3 text-left border-b border-gray-700 
                  transition-colors duration-150
                  ${isSelected 
                    ? 'bg-blue-600 text-white' 
                    : isHovered 
                      ? 'bg-gray-700' 
                      : 'bg-gray-800 text-gray-200'
                  }
                  hover:bg-gray-700
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset
                `}
              >
                <div className="flex items-center justify-between">
                  {/* Animation Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                      {/* Play Icon for Selected */}
                      {isSelected && (
                        <svg
                          className="w-4 h-4 mr-2 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                        </svg>
                      )}
                      
                      {/* Animation Name */}
                      <span className={`
                        font-medium truncate
                        ${isSelected ? 'text-white' : 'text-gray-200'}
                      `}>
                        {animation.name}
                      </span>

                      {/* Source Badge */}
                      {isRetargeted && (
                        <span className="ml-2 px-2 py-0.5 text-xs bg-purple-600 text-white rounded">
                          Retargeted
                        </span>
                      )}
                    </div>

                    {/* Metadata */}
                    <div className={`
                      flex items-center mt-1 text-xs space-x-3
                      ${isSelected ? 'text-blue-100' : 'text-gray-400'}
                    `}>
                      <span className="flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {formatDuration(animation.duration)}
                      </span>
                      <span className="flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                        </svg>
                        {animation.frameCount} frames
                      </span>
                    </div>
                  </div>

                  {/* Chevron */}
                  <svg
                    className={`
                      w-5 h-5 flex-shrink-0 ml-2 transition-transform
                      ${isSelected ? 'text-white' : 'text-gray-400'}
                    `}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>

              {/* Save Animation Button - Only for retargeted animations */}
              {isRetargeted && jobId && (
                <div className="absolute top-2 right-10 z-10">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSaveAnimation(animation);
                    }}
                    disabled={isSaving}
                    className={`
                      px-3 py-1 text-xs font-medium rounded transition-colors
                      ${isSaving 
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                        : isSelected
                          ? 'bg-blue-700 hover:bg-blue-800 text-white'
                          : 'bg-green-600 hover:bg-green-700 text-white'
                      }
                      focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-800
                    `}
                    title="Save this animation permanently to the model file"
                  >
                    {isSaving ? (
                      <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Saving...
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                        </svg>
                        Save
                      </span>
                    )}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="px-4 py-2 bg-gray-900 border-t border-gray-700">
        <p className="text-xs text-gray-400">
          Select an animation to preview playback
        </p>
      </div>

      {/* Playback Controls - shown when animation is selected */}
      {selectedAnimation && onPlay && onPause && onStop && onSeek && (
        <div className="border-t border-gray-700 p-3 bg-gray-900">
          <PlaybackControls
            isPlaying={isPlaying}
            currentTime={currentTime}
            duration={selectedAnimation.duration}
            onPlay={onPlay}
            onPause={onPause}
            onStop={onStop}
            onSeek={onSeek}
            playbackSpeed={playbackSpeed}
            onSpeedChange={onSpeedChange}
            isLooping={isLooping}
            onLoopToggle={onLoopToggle}
          />
        </div>
      )}

      {/* Motion Retargeting Modal */}
      <Modal
        isOpen={showRetargetModal}
        onClose={handleCloseRetargetModal}
        title="Retarget Motion"
        size="xl"
        closeOnBackdropClick={!isRetargeting}
        closeOnEscape={!isRetargeting}
      >
        <div className="space-y-4">
          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
            <p className="font-medium mb-1">Select a motion clip to apply to your rigged model</p>
            <p className="text-xs">
              The motion will be retargeted to match your model's skeleton structure.
              This process typically takes 30-60 seconds.
            </p>
          </div>

          {/* Motion Clips Browser */}
          <div className="max-h-[500px] overflow-auto">
            <MotionClipsBrowser
              onSelectClip={handleSelectMotionClip}
              selectedClipId={selectedMotionClip?.id}
            />
          </div>

          {/* Selected Clip Info */}
          {selectedMotionClip && !isRetargeting && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Selected Motion</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-600">Name:</span>
                  <span className="ml-2 font-medium">{selectedMotionClip.name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Duration:</span>
                  <span className="ml-2 font-medium">{selectedMotionClip.duration.toFixed(2)}s</span>
                </div>
                <div>
                  <span className="text-gray-600">Skeleton:</span>
                  <span className="ml-2 font-medium capitalize">{selectedMotionClip.skeletonType}</span>
                </div>
                <div>
                  <span className="text-gray-600">Bones:</span>
                  <span className="ml-2 font-medium">{selectedMotionClip.boneCount}</span>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 pt-3 border-t">
            <button
              onClick={handleCloseRetargetModal}
              disabled={isRetargeting}
              className={`
                px-4 py-2 text-sm font-medium rounded
                ${isRetargeting
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              {isRetargeting ? 'Processing...' : 'Cancel'}
            </button>
            <button
              onClick={handleApplyRetargeting}
              disabled={!selectedMotionClip || isRetargeting}
              className={`
                px-4 py-2 text-sm font-medium rounded
                ${!selectedMotionClip || isRetargeting
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
                }
              `}
            >
              {isRetargeting ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Retargeting ({retargetingProgress}%)
                </span>
              ) : (
                'Apply Motion'
              )}
            </button>
          </div>
        </div>
      </Modal>

      {/* Success Notification Toast */}
      {showSuccessNotification && (
        <div className="fixed bottom-4 right-4 z-50 animate-slide-up">
          <div className="bg-green-600 text-white px-6 py-4 rounded-lg shadow-2xl flex items-start space-x-3 max-w-md">
            <svg className="w-6 h-6 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h4 className="font-semibold mb-1">Retargeting Complete!</h4>
              <p className="text-sm text-green-100">
                "{completedMotionName}" has been successfully applied to your model.
              </p>
            </div>
            <button
              onClick={() => setShowSuccessNotification(false)}
              className="text-green-100 hover:text-white transition-colors"
              aria-label="Close notification"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Save Success Notification */}
      {saveSuccess && (
        <div className="fixed bottom-4 right-4 z-50 animate-slide-up">
          <div className="bg-green-600 text-white px-6 py-4 rounded-lg shadow-2xl flex items-start space-x-3 max-w-md">
            <svg className="w-6 h-6 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h4 className="font-semibold mb-1">Animation Saved!</h4>
              <p className="text-sm text-green-100">
                {saveSuccess}
              </p>
            </div>
            <button
              onClick={() => setSaveSuccess(null)}
              className="text-green-100 hover:text-white transition-colors"
              aria-label="Close notification"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Save Error Notification */}
      {saveError && (
        <div className="fixed bottom-4 right-4 z-50 animate-slide-up">
          <div className="bg-red-600 text-white px-6 py-4 rounded-lg shadow-2xl flex items-start space-x-3 max-w-md">
            <svg className="w-6 h-6 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h4 className="font-semibold mb-1">Save Failed</h4>
              <p className="text-sm text-red-100">
                {saveError}
              </p>
            </div>
            <button
              onClick={() => setSaveError(null)}
              className="text-red-100 hover:text-white transition-colors"
              aria-label="Close notification"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Skeleton Compatibility Error Modal */}
      {compatibilityError && (
        <Modal
          isOpen={true}
          onClose={() => setCompatibilityError(null)}
          title="Skeleton Incompatibility"
          size="lg"
        >
          <div className="space-y-4">
            {/* Error Header */}
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-start space-x-3">
              <svg className="w-6 h-6 text-orange-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-orange-900 mb-1">Motion Cannot Be Applied</h4>
                <p className="text-sm text-orange-800">{compatibilityError.message}</p>
              </div>
            </div>

            {/* Compatibility Score */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Compatibility Score</span>
                <span className={`text-lg font-bold ${
                  compatibilityError.compatibility.compatibilityScore >= 0.7 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {(compatibilityError.compatibility.compatibilityScore * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    compatibilityError.compatibility.compatibilityScore >= 0.7
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${compatibilityError.compatibility.compatibilityScore * 100}%` }}
                />
              </div>
              <p className="text-xs text-gray-600 mt-2">
                Minimum compatibility required: 70%
              </p>
            </div>

            {/* Skeleton Types */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 rounded-lg p-3">
                <h5 className="text-xs font-semibold text-blue-900 mb-1">Motion Skeleton</h5>
                <p className="text-sm text-blue-800 capitalize">{compatibilityError.compatibility.sourceType}</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <h5 className="text-xs font-semibold text-purple-900 mb-1">Your Model Skeleton</h5>
                <p className="text-sm text-purple-800 capitalize">{compatibilityError.compatibility.targetType}</p>
              </div>
            </div>

            {/* Matched Bones */}
            {compatibilityError.compatibility.matchedBones.length > 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <h5 className="text-xs font-semibold text-green-900 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Matched Bones ({compatibilityError.compatibility.matchedBones.length})
                </h5>
                <div className="flex flex-wrap gap-1">
                  {compatibilityError.compatibility.matchedBones.slice(0, 10).map((bone, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded">
                      {bone}
                    </span>
                  ))}
                  {compatibilityError.compatibility.matchedBones.length > 10 && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded">
                      +{compatibilityError.compatibility.matchedBones.length - 10} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Missing Bones */}
            {compatibilityError.compatibility.missingBones.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <h5 className="text-xs font-semibold text-red-900 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Missing Bones ({compatibilityError.compatibility.missingBones.length})
                </h5>
                <p className="text-xs text-red-700 mb-2">
                  These bones are required by the motion but not found in your model:
                </p>
                <div className="flex flex-wrap gap-1">
                  {compatibilityError.compatibility.missingBones.map((bone, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded">
                      {bone}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Extra Bones */}
            {compatibilityError.compatibility.extraBones.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <h5 className="text-xs font-semibold text-yellow-900 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  Extra Bones ({compatibilityError.compatibility.extraBones.length})
                </h5>
                <p className="text-xs text-yellow-700 mb-2">
                  These bones exist in your model but are not used by the motion:
                </p>
                <div className="flex flex-wrap gap-1">
                  {compatibilityError.compatibility.extraBones.slice(0, 10).map((bone, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded">
                      {bone}
                    </span>
                  ))}
                  {compatibilityError.compatibility.extraBones.length > 10 && (
                    <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded">
                      +{compatibilityError.compatibility.extraBones.length - 10} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Suggestions */}
            {compatibilityError.suggestions.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <h5 className="text-xs font-semibold text-blue-900 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Suggestions
                </h5>
                <ul className="space-y-1">
                  {compatibilityError.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="text-sm text-blue-800 flex items-start">
                      <span className="mr-2">•</span>
                      <span>{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-3 border-t">
              <button
                onClick={() => setCompatibilityError(null)}
                className="px-4 py-2 text-sm font-medium bg-white text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setCompatibilityError(null);
                  setShowRetargetModal(true);
                }}
                className="px-4 py-2 text-sm font-medium bg-purple-600 text-white rounded hover:bg-purple-700"
              >
                Try Different Motion
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
