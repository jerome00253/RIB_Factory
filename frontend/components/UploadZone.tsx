import { Icon } from '@iconify/react';
import { useCallback, useState } from 'react';

interface UploadZoneProps {
  onFileSelect: (files: File[]) => void;
  isProcessing: boolean;
}

export function UploadZone({ onFileSelect, isProcessing }: UploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      // Convert FileList to Array
      const filesArray = Array.from(e.dataTransfer.files);
      onFileSelect(filesArray);
    }
  }, [onFileSelect]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      const filesArray = Array.from(e.target.files);
      onFileSelect(filesArray);
    }
  };

  return (
    <div 
      className={`relative w-full max-w-xl mx-auto rounded-2xl p-12 text-center transition-all duration-500 ease-out cursor-pointer group overflow-hidden
        ${isProcessing ? 'opacity-50 pointer-events-none' : ''}
      `}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      {/* Gradient border effect */}
      <div className={`absolute inset-0 rounded-2xl transition-all duration-300 ${
        dragActive 
          ? 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 p-[3px]' 
          : 'bg-gradient-to-r from-gray-300 via-gray-300 to-gray-300 group-hover:from-blue-400 group-hover:via-purple-400 group-hover:to-pink-400 p-[2px]'
      }`}>
        <div className={`w-full h-full rounded-2xl transition-all duration-300 ${
          dragActive 
            ? 'bg-gradient-to-br from-blue-50 to-purple-50' 
            : 'bg-white group-hover:bg-gradient-to-br group-hover:from-gray-50 group-hover:to-blue-50'
        }`}></div>
      </div>

      <input 
        type="file" 
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
        onChange={handleChange}
        accept="image/*,application/pdf"
        disabled={isProcessing}
        multiple
      />
      
      <div className="relative z-0 flex flex-col items-center justify-center space-y-5 pointer-events-none">
        <div className={`p-5 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-200/50 transition-all duration-300 group-hover:scale-110 group-hover:shadow-xl group-hover:shadow-purple-300/50 ${dragActive ? 'scale-125 shadow-2xl shadow-purple-400/60' : ''}`}>
           {isProcessing ? (
             <Icon icon="line-md:loading-loop" className="w-10 h-10 animate-spin" />
           ) : (
             <Icon icon="mdi:folder-multiple-image" className="w-10 h-10" />
           )}
        </div>
        
        <div className="space-y-2">
          <p className="text-lg font-bold text-gray-800">
            {isProcessing ? 'Traitement en cours...' : 'Glissez-déposez vos RIBs'}
          </p>
          {!isProcessing && (
            <>
              <p className="text-sm text-gray-600 font-medium">
                 ou cliquez pour sélectionner
              </p>
              <p className="text-xs text-gray-500 mt-1">
                 Supporte Images & PDF • Max 24 fichiers
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
