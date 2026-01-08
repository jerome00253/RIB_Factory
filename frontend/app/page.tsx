"use client";

import { Icon } from '@iconify/react';
import { useState } from 'react';
import { UploadZone } from '../components/UploadZone';
import { RibResult } from '../components/RibResult';
import { RibTable } from '../components/RibTable';
import { RibDetailModal } from '../components/RibDetailModal';
import { analyzeRib, AnalyzeResponse } from '../lib/api';
import * as XLSX from 'xlsx';

interface ProcessedFile {
  file: File;
  status: 'pending' | 'processing' | 'done' | 'error';
  response: AnalyzeResponse | null;
  error?: string;
}

export default function Home() {
  const [items, setItems] = useState<ProcessedFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedItemIndex, setSelectedItemIndex] = useState<number | null>(null);

  const handleFilesSelect = (files: File[]) => {
    const newItems: ProcessedFile[] = files.map(file => ({
      file,
      status: 'pending',
      response: null
    }));
    // Capture current length BEFORE appending
    const currentLength = items.length;
    // Append to existing items instead of replacing
    setItems(prev => [...prev, ...newItems]);
    processQueue(newItems, currentLength);
  };

  const processQueue = async (queue: ProcessedFile[], startIndex: number) => {
    setIsProcessing(true);
    for (let i = 0; i < queue.length; i++) {
        const file = queue[i].file;
        const actualIndex = startIndex + i;
        setItems(prev => prev.map((item, idx) => idx === actualIndex ? { ...item, status: 'processing' } : item));
        try {
            const result = await analyzeRib(file);
            setItems(prev => prev.map((item, idx) => idx === actualIndex ? { ...item, status: 'done', response: result } : item));
        } catch (err: any) {
             const errorMsg = err.message || "Erreur inconnue";
             setItems(prev => prev.map((item, idx) => idx === actualIndex ? { ...item, status: 'error', error: errorMsg } : item));
        }
    }
    setIsProcessing(false);
  };

  const handleDeleteAll = () => {
    if (confirm('Êtes-vous sûr de vouloir supprimer tous les scans ?')) {
      setItems([]);
      setSelectedItemIndex(null);
    }
  };

  const handleDelete = (index: number) => {
    if (confirm('Supprimer ce scan ?')) {
      setItems(prev => prev.filter((_, idx) => idx !== index));
      if (selectedItemIndex === index) {
        setSelectedItemIndex(null);
      }
    }
  };

  const handleExport = () => {
    if (items.length === 0) return;

    const data = items.map(item => ({
        'Fichier': item.file.name,
        'Statut': item.status,
        'Titulaire': item.response?.data.owner_name || (item.error ? 'Erreur' : ''),
        'IBAN': item.response?.data.iban || '',
        'BIC': item.response?.data.bic || '',
        'Banque': item.response?.data.bank_name || '',
        'Score (%)': item.response?.confidence_score || 0,
        'Méthode': item.response?.extraction_method || '',
        'Checksum Valide': item.response?.checksum_valid ? 'OUI' : 'NON'
    }));

    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(data);
    
    const wscols = [
        {wch: 30}, {wch: 10}, {wch: 25}, {wch: 30}, {wch: 12}, 
        {wch: 20}, {wch: 10}, {wch: 25}, {wch: 15}
    ];
    ws['!cols'] = wscols;

    XLSX.utils.book_append_sheet(wb, ws, "Résultats RIB");
    XLSX.writeFile(wb, `RIB_Export_${new Date().toISOString().slice(0,10)}.xlsx`);
  };

  const hasResults = items.length > 0;
  const completedCount = items.filter(i => i.status === 'done' || i.status === 'error').length;

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 text-gray-900 font-sans pb-20">
      
       <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-blue-400 to-cyan-300 rounded-full blur-3xl opacity-20 -translate-y-1/2 translate-x-1/3 animate-pulse"></div>
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-gradient-to-tr from-purple-400 to-pink-300 rounded-full blur-3xl opacity-20 translate-y-1/3 -translate-x-1/3 animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-gradient-to-r from-indigo-400 to-blue-300 rounded-full blur-3xl opacity-10 -translate-x-1/2 -translate-y-1/2"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-8 pt-8">
        
        <header className="flex items-center justify-between mb-12 animate-fade-in-down">
             <div className="flex items-center gap-4">
                 <div className="p-3 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl shadow-lg shadow-blue-200/50 text-white">
                    <Icon icon="mdi:bank-transfer" className="w-10 h-10" />
                 </div>
                 <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">RIB Factory</h1>
                    <p className="text-sm text-gray-600 font-medium">Extraction de masse (OCR)</p>
                 </div>
             </div>
        </header>

        <div className="space-y-8 animate-fade-in-up">
            
            {!hasResults ? (
                <div className="max-w-2xl mx-auto mt-20">
                    <div className="text-center mb-10">
                        <h2 className="text-4xl font-extrabold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-4">Traitement par Lot</h2>
                        <p className="text-gray-600 text-lg max-w-xl mx-auto leading-relaxed">
                             Importez jusqu'à <span className="font-semibold text-blue-600">24 fichiers</span> (PDF ou Images) simultanément.
                             Notre moteur les traitera un par un pour garantir la stabilité.
                        </p>
                    </div>
                    <div className="bg-white/60 backdrop-blur-sm p-3 rounded-3xl shadow-xl border border-white/20">
                        <UploadZone onFileSelect={handleFilesSelect} isProcessing={isProcessing} />
                    </div>
                </div>
            ) : (
                <div className="space-y-6">
                    
                    <div className="flex items-center justify-between bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                         <div className="flex items-center gap-4">
                             <h2 className="font-bold text-lg flex items-center gap-2">
                                 File d'attente
                                 <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs">
                                     {completedCount} / {items.length}
                                 </span>
                             </h2>
                             {isProcessing && (
                                 <div className="flex items-center gap-2 text-sm text-blue-600 animate-pulse">
                                     <Icon icon="mdi:loading" className="animate-spin" />
                                     Traitement en cours...
                                 </div>
                             )}
                         </div>

                         <div className="flex items-center gap-3">
                            <button 
                                onClick={handleExport}
                                disabled={completedCount === 0}
                                className="px-4 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Icon icon="mdi:microsoft-excel" className="w-4 h-4 text-green-600" />
                                Exporter Excel
                            </button>

                            <button 
                                onClick={handleDeleteAll}
                                disabled={items.length === 0}
                                className="px-4 py-2 bg-red-50 border border-red-200 hover:bg-red-100 text-red-700 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Icon icon="mdi:delete-sweep" className="w-4 h-4" />
                                Tout supprimer
                            </button>

                            {!isProcessing && (
                                <label className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm shadow-blue-200 cursor-pointer">
                                    <Icon icon="mdi:plus" className="w-4 h-4" />
                                    Ajouter au lot
                                    <input 
                                        type="file" 
                                        className="hidden" 
                                        onChange={(e) => {
                                            if (e.target.files && e.target.files.length > 0) {
                                                handleFilesSelect(Array.from(e.target.files));
                                                e.target.value = ''; // Reset input
                                            }
                                        }}
                                        accept="image/*,application/pdf"
                                        multiple
                                    />
                                </label>
                            )}
                         </div>
                    </div>

                    <RibTable 
                        results={items} 
                        onShowDetail={(index) => setSelectedItemIndex(index)}
                        onDelete={handleDelete}
                    />

                </div>
            )}

        </div>
      </div>

       {selectedItemIndex !== null && items[selectedItemIndex] && (
        <RibDetailModal
            file={items[selectedItemIndex].file}
            result={items[selectedItemIndex].response}
            onClose={() => setSelectedItemIndex(null)}
        />
      )}

    </main>
  );
}
