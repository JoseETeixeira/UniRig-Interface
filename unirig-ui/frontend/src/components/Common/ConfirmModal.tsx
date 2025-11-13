import React from 'react';
import { Modal } from './Modal';
import { Button } from './Button';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  isLoading?: boolean;
}

/**
 * Confirmation modal for destructive actions
 */
export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false,
}) => {
  const getIconAndColors = () => {
    switch (variant) {
      case 'danger':
        return {
          icon: '⚠️',
          bgColor: 'bg-red-50',
          textColor: 'text-red-800',
          buttonVariant: 'danger' as const,
        };
      case 'warning':
        return {
          icon: '⚡',
          bgColor: 'bg-yellow-50',
          textColor: 'text-yellow-800',
          buttonVariant: 'primary' as const,
        };
      case 'info':
        return {
          icon: 'ℹ️',
          bgColor: 'bg-blue-50',
          textColor: 'text-blue-800',
          buttonVariant: 'primary' as const,
        };
    }
  };

  const { icon, bgColor, textColor, buttonVariant } = getIconAndColors();

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="" size="sm">
      <div className={`${bgColor} rounded-lg p-6`}>
        <div className="flex items-start gap-4">
          <div className="text-4xl">{icon}</div>
          <div className="flex-1">
            <h3 className={`${textColor} font-semibold text-lg mb-2`}>
              {title}
            </h3>
            <p className={`${textColor} text-sm mb-4`}>
              {message}
            </p>
            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                size="md"
                onClick={onClose}
                disabled={isLoading}
              >
                {cancelText}
              </Button>
              <Button
                variant={buttonVariant}
                size="md"
                onClick={onConfirm}
                disabled={isLoading}
                loading={isLoading}
              >
                {confirmText}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};
