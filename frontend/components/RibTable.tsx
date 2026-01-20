import { useState, useEffect } from 'react';
import { Icon } from '@iconify/react';
import { AnalyzeResponse } from '../lib/api';
import { formatIBAN } from '../lib/formatters'; // Add missing import

interface ProcessedFile {
  id: string;
  file: File;
  status: 'pending' | 'processing' | 'done' | 'error';
  response: AnalyzeResponse | null;
  error?: string;
}

interface RibTableProps {
  results: ProcessedFile[];
  onShowDetail: (index: number) => void;
  onDelete: (index: number) => void;
}

export function RibTable({ results, onShowDetail, onDelete }: RibTableProps) {
  return (
    <div className="w-full bg-white/80 backdrop-blur-md rounded-2xl shadow-2xl overflow-hidden border border-white/30">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gradient-to-r from-gray-50 to-blue-50/30 border-b-2 border-blue-100">
            <tr>
              <th className="px-6 py-4 font-bold text-gray-800 text-sm">Aperçu</th>
              <th className="px-6 py-4 font-bold text-gray-800 text-sm">Fichier</th>
              <th className="px-6 py-4 font-bold text-gray-800 text-sm">Titulaire</th>
              <th className="px-6 py-4 font-bold text-gray-800 text-sm">Détails Bancaires</th>
              <th className="px-6 py-4 font-bold text-gray-800 text-sm">Fiabilité</th>
              <th className="px-6 py-4 font-bold text-gray-800 text-sm text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {results.map((item, index) => {
              const { response, error, file } = item;
              
              if (error) {
                 return (
                    <tr key={index} className="hover:bg-red-50/50">
                        <td className="px-6 py-4">
                            <FileThumbnail file={file} onClick={() => onShowDetail(index)} />
                        </td>
                        <td className="px-6 py-4 font-medium text-gray-900 truncate max-w-[150px]">{file.name}</td>
                        <td colSpan={4} className="px-6 py-4 text-red-500 italic">{error}</td>
                        <td className="px-6 py-4 text-right"></td>
                    </tr>
                 )
              }
              
              if (!response) {
                  return (
                    <tr key={index} className="animate-pulse">
                        <td className="px-6 py-4">
                             <div className="w-12 h-12 bg-gray-200 rounded-lg animate-pulse" />
                        </td>
                        <td className="px-6 py-4">
                            <div className="font-semibold text-sm text-gray-900 truncate" title={item.file.name}>
                              {item.file.name}
                              {item.response?.page_number && <span className="text-gray-500 ml-1">(Page {item.response.page_number})</span>}
                            </div>
                            <div className="text-xs text-gray-500">{(item.file.size / 1024).toFixed(0)} KB</div>
                        </td>
                        <td colSpan={4} className="px-6 py-4 text-gray-400 italic">Analyse en cours...</td>
                    </tr>
                  )
              }

              const isSuccess = response.status === 'valid';
              const isWarning = response.status === 'warning';
              
              return (
                <tr key={index} className="hover:bg-gray-50 transition-colors group">
                  <td className="px-6 py-4">
                      <FileThumbnail file={file} onClick={() => onShowDetail(index)} />
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-900 truncate max-w-[150px]" title={file.name}>
                    {file.name}
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    <div className="flex items-center gap-2 group/owner">
                      <div className="font-medium text-gray-900">
                        {response.data.owner_name !== "Unknown" ? response.data.owner_name : <span className="text-gray-400 italic">Inconnu</span>}
                      </div>
                      {response.data.owner_name && response.data.owner_name !== "Unknown" && (
                        <button 
                          onClick={() => {
                            navigator.clipboard.writeText(response.data.owner_name || '');
                          }}
                          className="opacity-0 group-hover/owner:opacity-100 p-1 text-gray-400 hover:text-blue-600 transition-all rounded"
                          title="Copier le titulaire"
                        >
                          <Icon icon="mdi:content-copy" className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col space-y-1.5 w-full">
                         <DataRow label="IBAN" value={response.data.iban} displayValue={formatIBAN(response.data.iban)} />
                         <DataRow label="BIC" value={response.data.bic} />
                         <DataRow label="BANQUE" value={response.data.bank_name} />
                    </div>
                  </td>
                 <td className="px-6 py-4">
                    <div className="flex flex-col space-y-1">
                        <div className="flex items-center space-x-1.5">
                             <StatusBadge method={response.extraction_method} status={response.status} />
                        </div>
                        <div className="flex items-center space-x-1.5 pt-1">
                             <Icon icon={response.checksum_valid ? "mdi:check-decagram" : "mdi:alert-circle-outline"} className={response.checksum_valid ? "text-green-500 w-3.5 h-3.5" : "text-red-500 w-3.5 h-3.5"} />
                             <span className={`text-[10px] uppercase font-bold tracking-wider ${response.checksum_valid ? "text-green-600" : "text-red-500"}`}>
                                {response.checksum_valid ? "Checksum OK" : "Checksum Invalid"}
                             </span>
                        </div>
                        {response.rib_key_valid !== null && response.rib_key_valid !== undefined && (
                          <div className="flex items-center space-x-1.5 pt-1">
                               <Icon icon={response.rib_key_valid ? "mdi:key-check" : "mdi:key-remove"} className={response.rib_key_valid ? "text-green-500 w-3.5 h-3.5" : "text-orange-500 w-3.5 h-3.5"} />
                               <span className={`text-[10px] uppercase font-bold tracking-wider ${response.rib_key_valid ? "text-green-600" : "text-orange-500"}`}>
                                  {response.rib_key_valid ? "Clé OK" : "Clé Invalid"}
                               </span>
                          </div>
                        )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">
                      <button 
                          onClick={() => onDelete(index)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Supprimer"
                      >
                          <Icon icon="mdi:delete-outline" className="w-5 h-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FileThumbnail({ file, onClick }: { file: File, onClick: () => void }) {
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreview(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [file]);

  return (
    <div 
      onClick={onClick}
      className="w-12 h-12 rounded-lg border border-gray-200 overflow-hidden cursor-pointer hover:ring-2 hover:ring-blue-400 hover:shadow-md transition-all bg-gray-50 flex items-center justify-center group/thumb relative"
      title="Voir l'aperçu"
    >
      {file.type.startsWith('image/') && preview ? (
        <img src={preview} alt="Aperçu" className="w-full h-full object-cover" />
      ) : (
        <Icon icon="mdi:file-pdf-box" className="w-8 h-8 text-red-500 group-hover/thumb:scale-110 transition-transform" />
      )}
      <div className="absolute inset-0 bg-black/0 group-hover/thumb:bg-black/10 transition-colors" />
    </div>
  );
}

function StatusBadge({ method, status }: { method: string | undefined | null, status: string }) {
    if (!method) return <span className="text-xs text-gray-400">N/A</span>;

    let icon = "mdi:eye-check-outline";
    let color = "text-gray-600";
    let text = method;
    let bg = "bg-gray-100";
    
    // Normalize string
    const m = method.toLowerCase();

    if (m.includes("direct")) {
        icon = "mdi:target-variant";
        color = "text-green-700";
        bg = "bg-green-100";
        text = "Extr. Directe";
    } else if (m.includes("correction")) {
        icon = "mdi:auto-fix";
        color = "text-blue-700";
        bg = "bg-blue-100";
        text = "Corr. OCR";
    } else if (m.includes("reconstructed")) {
        // Reconstructed
        if (m.includes("found in text")) {
            icon = "mdi:puzzle-check";
            color = "text-teal-700";
            bg = "bg-teal-100";
            text = "Reconstruit (Prouvé)";
        } else {
            icon = "mdi:puzzle-alert";
            color = "text-orange-700";
            bg = "bg-orange-100";
            text = "Reconstruit (Non prouvé)";
        }
    }

    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold shadow-sm border ${bg} ${color}`}>
            <Icon icon={icon} className="w-3.5 h-3.5" />
            {text}
        </span>
    )
}



interface DataRowProps {
    label: string;
    value: string | null | undefined;
    displayValue?: string;
}

function DataRow({ label, value, displayValue }: DataRowProps) {
    const handleCopy = (e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent row click
        if (value) {
            navigator.clipboard.writeText(value);
            // Optional: visual feedback via toast?
        }
    };

    return (
        <div className="flex items-center group/row">
             <span className="text-[10px] font-bold text-gray-400 w-14 uppercase tracking-wider">{label}</span>
             <div className="flex items-center gap-2 flex-1 min-w-0">
                 <span className={`text-xs truncate ${!value ? "text-gray-300 italic" : "text-gray-700 font-mono"}`}>
                    {displayValue || value || "N/A"}
                 </span>
                 {value && (
                    <button 
                        onClick={handleCopy}
                        className="opacity-0 group-hover/row:opacity-100 text-gray-400 hover:text-blue-600 transition-opacity p-0.5"
                        title="Copier"
                    >
                        <Icon icon="mdi:content-copy" className="w-3 h-3" />
                    </button>
                 )}
             </div>
        </div>
    );
}
