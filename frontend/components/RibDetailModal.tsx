import { Icon } from '@iconify/react';
import { AnalyzeResponse } from '../lib/api';
import { useState, useEffect } from 'react';

interface RibDetailModalProps {
  file: File;
  result: AnalyzeResponse | null;
  onClose: () => void;
}

export function RibDetailModal({ file, result, onClose }: RibDetailModalProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isImageFullscreen, setIsImageFullscreen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    if (!file) return;
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 0.25, 0.5));
  const handleZoomReset = () => setZoomLevel(1);
  
  const handleWheel = (e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      if (e.deltaY < 0) {
        handleZoomIn();
      } else {
        handleZoomOut();
      }
    }
  };

  if (!result) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden animate-scale-in border border-white/50">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center space-x-3">
             <div className="p-2.5 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl text-white shadow-lg shadow-blue-200/50">
                <Icon icon="mdi:file-document-outline" className="w-6 h-6" />
             </div>
             <div>
                <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">{file.name}</h3>
                <p className="text-sm text-gray-600">Détail de l'analyse</p>
             </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/80 rounded-full transition-colors text-gray-600 hover:text-gray-900">
            <Icon icon="mdi:close" className="w-6 h-6" />
          </button>
        </div>

        {/* Content (Scrollable) */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col md:flex-row gap-6">
            
            {/* Left: Image/PDF Preview */}
            <div className="w-full md:w-1/2 bg-gray-100 rounded-xl border border-gray-200 flex items-center justify-center relative overflow-hidden min-h-[300px]">
                {file.type === 'application/pdf' ? (
                    previewUrl ? (
                      <>
                        <iframe 
                          src={previewUrl} 
                          className="absolute inset-0 w-full h-full"
                          title="Aperçu PDF"
                        />
                        <button
                          onClick={() => window.open(previewUrl, '_blank')}
                          className="absolute top-2 right-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg shadow-lg flex items-center gap-2 text-sm font-medium transition-colors z-10"
                          title="Ouvrir en plein écran pour zoomer"
                        >
                          <Icon icon="mdi:open-in-new" className="w-4 h-4" />
                          Ouvrir pour zoomer
                        </button>
                      </>
                    ) : null
                ) : (
                    previewUrl && (
                      <div className="relative w-full h-full group">
                        <img 
                          src={previewUrl} 
                          alt="Scan" 
                          className="absolute inset-0 w-full h-full object-contain p-2 cursor-zoom-in" 
                          onClick={() => setIsImageFullscreen(true)}
                        />
                        <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                          <Icon icon="mdi:magnify-plus" className="w-4 h-4" />
                          Cliquer pour agrandir
                        </div>
                      </div>
                    )
                )}
            </div>

            {/* Right: Data */}
            <div className="w-full md:w-1/2 space-y-6">
                {/* Status Card */}
                <div className={`p-4 rounded-xl border ${result.status === 'valid' ? 'bg-green-50 border-green-100 text-green-800' : 'bg-orange-50 border-orange-100 text-orange-800'}`}>
                    <div className="flex items-center justify-between">
                         <span className="font-bold uppercase flex items-center gap-2">
                             <Icon icon={result.status === 'valid' ? "mdi:check-circle" : "mdi:alert"} />
                             {result.status}
                         </span>
                         <span className="text-sm font-medium">{result.confidence_score.toFixed(1)}% Confiance</span>
                    </div>
                </div>

                 <div className="space-y-4">
                    <DetailRow label="IBAN" value={result.data.iban} copyable />
                    <DetailRow label="BIC" value={result.data.bic} copyable />
                    <DetailRow label="Titulaire" value={result.data.owner_name} copyable />
                    <DetailRow label="Banque" value={result.data.bank_name} copyable />
                 </div>

                 <div className="pt-4 border-t border-gray-100 space-y-2">
                     <p className="text-xs text-gray-500 flex justify-between">
                        <span>Méthode Extraction:</span>
                        <span className="font-medium text-gray-700">{result.extraction_method || "N/A"}</span>
                     </p>
                     <p className="text-xs text-gray-500 flex justify-between">
                        <span>Checksum IBAN:</span>
                        <span className={`font-medium ${result.checksum_valid ? "text-green-600" : "text-red-500"}`}>
                            {result.checksum_valid ? "Validé (Modulo 97)" : "Invalide"}
                        </span>
                     </p>
                     
                     {result.validation_details && result.validation_details.length > 0 && (
                        <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-100">
                            <h4 className="text-xs font-bold text-red-800 mb-1 flex items-center gap-1">
                                <Icon icon="mdi:alert-circle" /> Problèmes détectés :
                            </h4>
                            <ul className="list-disc list-inside text-xs text-red-700 space-y-0.5">
                                {result.validation_details.map((msg, i) => (
                                    <li key={i}>{msg}</li>
                                ))}
                            </ul>
                        </div>
                     )}
                 </div>
            </div>

        </div>

        {/* Footer */}
        <div className="p-4 bg-gradient-to-r from-gray-50 to-blue-50/30 border-t border-gray-100 text-right">
             <button 
                onClick={onClose}
                className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl transition-all duration-200 font-semibold text-sm shadow-lg shadow-blue-200/50 hover:shadow-xl hover:shadow-purple-300/50"
             >
                Fermer
             </button>
        </div>

      </div>

      {/* Fullscreen Image Modal */}
      {isImageFullscreen && !file.type.includes('pdf') && previewUrl && (
        <div 
          className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in"
          onClick={() => {
            setIsImageFullscreen(false);
            setZoomLevel(1);
          }}
          onWheel={handleWheel}
        >
          <button 
            onClick={() => {
              setIsImageFullscreen(false);
              setZoomLevel(1);
            }}
            className="absolute top-4 right-4 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white z-10"
            title="Fermer"
          >
            <Icon icon="mdi:close" className="w-6 h-6" />
          </button>

          {/* Zoom Controls */}
          <div className="absolute top-4 left-4 flex flex-col gap-2 z-10">
            <button 
              onClick={(e) => {
                e.stopPropagation();
                handleZoomIn();
              }}
              className="p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white"
              title="Zoom avant (Ctrl + molette)"
            >
              <Icon icon="mdi:magnify-plus" className="w-6 h-6" />
            </button>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                handleZoomOut();
              }}
              className="p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white"
              title="Zoom arrière (Ctrl + molette)"
            >
              <Icon icon="mdi:magnify-minus" className="w-6 h-6" />
            </button>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                handleZoomReset();
              }}
              className="p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white"
              title="Réinitialiser le zoom"
            >
              <Icon icon="mdi:magnify" className="w-6 h-6" />
            </button>
            <div className="px-3 py-2 bg-black/50 text-white rounded-full text-sm font-medium text-center">
              {(zoomLevel * 100).toFixed(0)}%
            </div>
          </div>

          <img 
            src={previewUrl} 
            alt="Scan en plein écran" 
            className="max-w-full max-h-full object-contain transition-transform duration-200"
            style={{ transform: `scale(${zoomLevel})` }}
            onClick={(e) => e.stopPropagation()}
          />
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/50 text-white px-4 py-2 rounded-full text-sm">
            Cliquer en dehors pour fermer • Ctrl + molette pour zoomer
          </div>
        </div>
      )}
    </div>
  );
}

function DetailRow({ label, value, copyable }: { label: string, value: string | null, copyable?: boolean }) {
    const handleCopy = () => { if(value) navigator.clipboard.writeText(value); }
    return (
        <div className="group flex items-start justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100">
            <span className="text-sm text-gray-500 font-medium pt-0.5">{label}</span>
            <div className="flex items-center gap-2 max-w-[70%]">
                <span className={`text-sm font-mono text-gray-900 break-all text-right ${!value && "opacity-50 italic"}`}>
                    {value || "Non trouvé"}
                </span>
                 {copyable && value && (
                    <button onClick={handleCopy} className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-blue-600">
                        <Icon icon="mdi:content-copy" className="w-4 h-4" />
                    </button>
                )}
            </div>
        </div>
    )
}
