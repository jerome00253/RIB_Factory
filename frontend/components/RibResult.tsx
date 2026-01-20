import { Icon } from '@iconify/react';
import { AnalyzeResponse, RibData } from '../lib/api';

interface RibResultProps {
  result: AnalyzeResponse;
  onReset: () => void;
}

export function RibResult({ result, onReset }: RibResultProps) {
  const { data, status, confidence_score } = result;

  const getStatusColor = () => {
    switch (status) {
      case 'valid': return 'text-green-600 bg-green-50 border-green-200';
      case 'warning': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'invalid': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getIcon = () => {
    switch (status) {
        case 'valid': return 'mdi:check-circle';
        case 'warning': return 'mdi:alert-circle';
        case 'invalid': return 'mdi:close-circle';
        default: return 'mdi:help-circle';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto rounded-2xl shadow-2xl border border-white/30 bg-white/90 backdrop-blur-md overflow-hidden animate-fade-in">
      {/* Header */}
      <div className={`p-6 border-b flex items-center justify-between ${getStatusColor()}`}>
        <div className="flex items-center space-x-3">
            <Icon icon={getIcon()} className="w-8 h-8" />
            <div>
                <h3 className="text-lg font-bold uppercase tracking-wide">{status}</h3>
                <p className="text-sm opacity-80">Score de confiance : {confidence_score.toFixed(1)}%</p>
                {result.extraction_method && (
                    <p className="text-xs opacity-70 mt-0.5 italic">
                       Méthode : {result.extraction_method}
                    </p>
                )}
                <p className="text-xs opacity-70 mt-0.5 flex items-center gap-1">
                   Checksum : 
                   <span className={result.checksum_valid ? "text-green-500 font-bold" : "text-red-400"}>
                     {result.checksum_valid ? "VALIDE (Mod 97)" : "INVALID"}
                   </span>
                </p>
            </div>
        </div>
        <button 
            onClick={onReset}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
            title="Nouvelle analyse"
        >
            <Icon icon="mdi:refresh" className="w-6 h-6" />
        </button>
      </div>

      {/* Content */}
      <div className="p-8 space-y-6">
        <DataRow label="IBAN" value={data.iban} copyable />
        <DataRow label="BIC" value={data.bic} copyable />
        <DataRow label="Banque" value={data.bank_name || "Non détectée"} />
        <DataRow label="Titulaire" value={data.owner_name || "Non détecté"} />
      </div>

      {/* Footer */}
      <div className="bg-gray-50 px-8 py-4 text-xs text-center text-gray-400 border-t">
        Données extraites automatiquement via DocTR. Vérifiez toujours avec l'original.
      </div>
    </div>
  );
}

function DataRow({ label, value, copyable = false }: { label: string, value: string | null, copyable?: boolean }) {
    const handleCopy = () => {
        if(value) navigator.clipboard.writeText(value);
    };

    return (
        <div className="group flex items-center justify-between py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 px-2 -mx-2 rounded transition-colors">
            <span className="text-sm font-medium text-gray-500 w-24">{label}</span>
            <div className="flex-1 flex items-center justify-end space-x-2">
                <span className={`font-mono text-gray-800 ${!value ? 'italic opacity-50' : ''}`}>
                    {value || "N/A"}
                </span>
                {copyable && value && (
                    <button 
                        onClick={handleCopy}
                        className="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-blue-600 transition-all"
                        title="Copier"
                    >
                        <Icon icon="mdi:content-copy" className="w-4 h-4" />
                    </button>
                )}
            </div>
        </div>
    )
}
