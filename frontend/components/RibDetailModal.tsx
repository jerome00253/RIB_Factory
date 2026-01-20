import { Icon } from '@iconify/react';
import { AnalyzeResponse } from '../lib/api'; // Restore missing import
import { formatIBAN } from '../lib/formatters'; // Add missing import
import { useState, useEffect, useRef } from 'react';

function ImagePanZoom({ src }: { src: string }) {
    const [scale, setScale] = useState(1);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const containerRef = useRef<HTMLDivElement>(null);

    const handleZoomIn = () => setScale(s => Math.min(s + 0.5, 5));
    const handleZoomOut = () => {
        setScale(s => {
            const newScale = Math.max(s - 0.5, 1);
            if (newScale === 1) setPosition({ x: 0, y: 0 }); // Reset pos on full zoom out
            return newScale;
        });
    };
    const handleReset = () => {
        setScale(1);
        setPosition({ x: 0, y: 0 });
    };

    const onWheel = (e: React.WheelEvent) => {
        e.stopPropagation();
        // Allow normal scroll if not zoomed or ctrl key not pressed? 
        // Let's make wheel always zoom for convenience in this specific container
        if (e.deltaY < 0) handleZoomIn();
        else handleZoomOut();
    };

    const onMouseDown = (e: React.MouseEvent) => {
        if (scale > 1) {
            setIsDragging(true);
            setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
        }
    };

    const onMouseMove = (e: React.MouseEvent) => {
        if (isDragging && scale > 1) {
            e.preventDefault();
            setPosition({
                x: e.clientX - dragStart.x,
                y: e.clientY - dragStart.y
            });
        }
    };

    const onMouseUp = () => setIsDragging(false);
    const onMouseLeave = () => setIsDragging(false);

    return (
        <div 
            className="w-full h-full relative overflow-hidden bg-gray-900 flex items-center justify-center"
            onWheel={onWheel}
        >
             {/* Controls */}
             <div className="absolute top-4 right-4 flex flex-col gap-2 z-20">
                <button onClick={handleZoomIn} className="p-2 bg-black/50 hover:bg-black/70 text-white rounded-lg transition-colors shadow-lg" title="Zoomer">
                    <Icon icon="mdi:plus" className="w-5 h-5" />
                </button>
                <button onClick={handleZoomOut} className="p-2 bg-black/50 hover:bg-black/70 text-white rounded-lg transition-colors shadow-lg" title="Dézoomer">
                    <Icon icon="mdi:minus" className="w-5 h-5" />
                </button>
                <button onClick={handleReset} className="p-2 bg-black/50 hover:bg-black/70 text-white rounded-lg transition-colors shadow-lg" title="Réinitialiser">
                    <Icon icon="mdi:fit-to-screen-outline" className="w-5 h-5" />
                </button>
             </div>

             {/* Image */}
             <div 
                ref={containerRef}
                className={`transition-transform duration-100 ease-out origin-center ${scale > 1 ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'}`}
                style={{ 
                    transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                }}
                onMouseDown={onMouseDown}
                onMouseMove={onMouseMove}
                onMouseUp={onMouseUp}
                onMouseLeave={onMouseLeave}
             >
                 <img 
                    src={src} 
                    alt="Preview" 
                    className="max-w-full max-h-full object-contain pointer-events-none select-none" // prevent native drag
                    style={{ maxHeight: '100%', maxWidth: '100%' }}
                 />
             </div>
             
             {/* Hint */}
             <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-black/40 text-white text-xs rounded-full pointer-events-none backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity">
                {scale === 1 ? "Molette pour zoomer" : "Glisser pour déplacer"} • {Math.round(scale * 100)}%
             </div>
        </div>
    );
}

interface RibDetailModalProps {
  file: File;
  result: AnalyzeResponse | null;
  onClose: () => void;
  onNext?: () => void;
  onPrevious?: () => void;
  onDelete?: () => void;
}

export function RibDetailModal({ file, result, onClose, onNext, onPrevious, onDelete }: RibDetailModalProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (!file) return;
    const objectUrl = URL.createObjectURL(file);
    
    // Append #page=X if result has a page number and it's a PDF
    if (file.type === 'application/pdf' && result?.page_number) {
        setPreviewUrl(`${objectUrl}#page=${result.page_number}`);
    } else {
        setPreviewUrl(objectUrl);
    }

    return () => URL.revokeObjectURL(objectUrl);
  }, [file, result]);

  if (!result) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden animate-scale-in border border-white/50 relative">
        
        {/* Confirmation Overlay for Deletion */}
        {showDeleteConfirm && (
            <div className="absolute inset-0 z-[60] bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
                <div className="bg-white rounded-3xl p-8 shadow-2xl max-w-sm w-full animate-scale-in border border-red-50">
                    <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Icon icon="mdi:alert-circle-outline" className="w-10 h-10" />
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 text-center mb-2">Supprimer cette page ?</h4>
                    <p className="text-gray-600 text-center mb-8">Cette action est irréversible pour ce scan spécifique.</p>
                    <div className="flex gap-3">
                        <button 
                            onClick={() => setShowDeleteConfirm(false)}
                            className="flex-1 px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-semibold transition-colors"
                        >
                            Annuler
                        </button>
                        <button 
                            onClick={() => {
                                onDelete?.();
                                setShowDeleteConfirm(false);
                            }}
                            className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-semibold transition-colors shadow-lg shadow-red-200"
                        >
                            Supprimer
                        </button>
                    </div>
                </div>
            </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center space-x-3">
             <div className="p-2.5 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl text-white shadow-lg shadow-blue-200/50">
                <Icon icon="mdi:file-document-outline" className="w-6 h-6" />
             </div>
             <div>
                <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">{file.name}</h3>
                <p className="text-sm text-gray-600">Détail de l'analyse {result.page_number ? `• Page ${result.page_number}` : ''}</p>
             </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/80 rounded-full transition-colors text-gray-600 hover:text-gray-900">
            <Icon icon="mdi:close" className="w-6 h-6" />
          </button>
        </div>

        {/* Content (Scrollable) */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col md:flex-row gap-6">
            
            {/* Left: Image/PDF Preview */}
            <div className="w-full md:w-2/3 bg-gray-900 rounded-xl border border-gray-200 flex items-center justify-center relative overflow-hidden min-h-[600px] group">
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
                          title="Ouvrir dans un nouvel onglet"
                        >
                          <Icon icon="mdi:open-in-new" className="w-4 h-4" />
                          Ouvrir
                        </button>
                      </>
                    ) : null
                ) : (
                    previewUrl && (
                      <ImagePanZoom src={previewUrl} />
                    )
                )}
            </div>

            {/* Right: Data */}
            <div className="w-full md:w-1/3 space-y-6">
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
                    <DetailRow label="IBAN" value={result.data.iban} displayValue={formatIBAN(result.data.iban)} copyable />
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
        <div className="p-4 bg-gradient-to-r from-gray-50 to-blue-50/30 border-t border-gray-100 flex items-center justify-between">
             <div className="flex gap-2">
                <button 
                  onClick={onPrevious}
                  disabled={!onPrevious}
                  className="px-4 py-2.5 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl transition-all font-semibold text-sm shadow-sm disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Icon icon="mdi:chevron-left" className="w-5 h-5" />
                  Précédent
                </button>
                <button 
                  onClick={onNext}
                  disabled={!onNext}
                  className="px-4 py-2.5 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl transition-all font-semibold text-sm shadow-sm disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  Suivant
                  <Icon icon="mdi:chevron-right" className="w-5 h-5" />
                </button>
             </div>

             <div className="flex gap-2 items-center">
                <button 
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2.5 bg-red-50 text-red-600 hover:bg-red-100 border border-red-100 rounded-xl transition-all font-semibold text-sm flex items-center gap-2 mr-4"
                >
                  <Icon icon="mdi:delete-outline" className="w-5 h-5" />
                  Supprimer
                </button>
                <button 
                    onClick={onClose}
                    className="px-8 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl transition-all duration-200 font-semibold text-sm shadow-lg shadow-blue-200/50"
                >
                    Fermer
                </button>
             </div>
        </div>

      </div>
    </div>
  );
}



function DetailRow({ label, value, displayValue, copyable }: { label: string, value: string | null, displayValue?: string, copyable?: boolean }) {
    const handleCopy = () => { if(value) navigator.clipboard.writeText(value); }
    return (
        <div className="group flex items-start justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100">
            <span className="text-sm text-gray-500 font-medium pt-0.5">{label}</span>
            <div className="flex items-center gap-2 max-w-[70%]">
                <span className={`text-sm font-mono text-gray-900 break-all text-right ${!value && "opacity-50 italic"}`}>
                    {displayValue || value || "Non trouvé"}
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
