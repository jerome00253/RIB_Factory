"use client";

import { Icon } from "@iconify/react";
import { useState } from "react";
import { UploadZone } from "../components/UploadZone";
import { RibResult } from "../components/RibResult";
import { RibTable } from "../components/RibTable";
import { RibDetailModal } from "../components/RibDetailModal";
import { analyzeRib, AnalyzeResponse } from "../lib/api";
import * as XLSX from "xlsx";

import { v4 as uuidv4 } from "uuid";

interface ProcessedFile {
  id: string;
  file: File;
  status: "pending" | "processing" | "done" | "error";
  response: AnalyzeResponse | null;
  error?: string;
}

export default function Home() {
  const [items, setItems] = useState<ProcessedFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [ibanFilter, setIbanFilter] = useState<
    "detected" | "not-detected" | "all"
  >("all");

  const handleFilesSelect = (files: File[]) => {
    const newItems: ProcessedFile[] = files.map((file) => ({
      id: uuidv4(),
      file,
      status: "pending",
      response: null,
    }));

    setItems((prev) => [...prev, ...newItems]);
    processQueue(newItems);
  };

  const processQueue = async (queue: ProcessedFile[]) => {
    setIsProcessing(true);

    for (const queueItem of queue) {
      setItems((prev) =>
        prev.map((item) =>
          item.id === queueItem.id ? { ...item, status: "processing" } : item,
        ),
      );

      try {
        let firstResult = true;
        await analyzeRib(queueItem.file, (res) => {
          setItems((prev) => {
            const index = prev.findIndex(
              (p) => p.id === queueItem.id && p.status === "processing",
            );

            if (firstResult && index !== -1) {
              // Replace the processing placeholder with the first real result
              firstResult = false;
              const newItems = [...prev];
              newItems[index] = {
                ...newItems[index],
                status: "done",
                response: res,
              };
              return newItems;
            } else {
              // Append additional results (for multi-page)
              return [
                ...prev,
                {
                  id: uuidv4(),
                  file: queueItem.file,
                  status: "done",
                  response: res,
                },
              ];
            }
          });
        });

        // If no results were returned but analyzeRib finished without error
        setItems((prev) =>
          prev.map((item) =>
            item.id === queueItem.id && item.status === "processing"
              ? { ...item, status: "done" }
              : item,
          ),
        );
      } catch (err: any) {
        console.error("DEBUG: Error in processQueue for item execution:", err);
        const errorMsg = err.message || "Erreur inconnue";
        setItems((prev) =>
          prev.map((item) =>
            item.id === queueItem.id
              ? { ...item, status: "error", error: errorMsg }
              : item,
          ),
        );
      }
    }
    setIsProcessing(false);
  };

  const handleDeleteAll = () => {
    if (confirm("Êtes-vous sûr de vouloir supprimer tous les scans ?")) {
      setItems([]);
      setSelectedItemId(null);
    }
  };

  const handleDelete = (index: number) => {
    if (confirm("Supprimer ce scan ?")) {
      const itemToDelete = items[index];
      setItems((prev) => prev.filter((_, idx) => idx !== index));
      if (selectedItemId === itemToDelete.id) {
        setSelectedItemId(null);
      }
    }
  };

  const handleDeleteNonDetected = () => {
    if (confirm("Supprimer tous les scans sans IBAN détecté ?")) {
      setItems((prev) =>
        prev.filter((item) => {
          const hasIban =
            item.response?.data?.iban && item.response.data.iban.length > 0;
          return hasIban || item.status !== "done"; // Keep those with IBAN or still processing/error
        }),
      );
    }
  };

  const handleExport = () => {
    // Get only the filtered items for export
    const itemsToExport = getFilteredItems();

    if (itemsToExport.length === 0) return;

    const data = itemsToExport.map((item) => ({
      Fichier:
        item.file.name +
        (item.response?.page_number
          ? ` (Page ${item.response.page_number})`
          : ""),
      Statut: item.status,
      Titulaire: item.response?.data.owner_name || (item.error ? "Erreur" : ""),
      IBAN: item.response?.data.iban || "",
      BIC: item.response?.data.bic || "",
      Banque: item.response?.data.bank_name || "",
      "Score (%)": item.response?.confidence_score || 0,
      Méthode: item.response?.extraction_method || "",
      "Checksum Valide": item.response?.checksum_valid ? "OUI" : "NON",
    }));

    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(data);

    const wscols = [
      { wch: 35 },
      { wch: 10 },
      { wch: 25 },
      { wch: 30 },
      { wch: 12 },
      { wch: 20 },
      { wch: 10 },
      { wch: 25 },
      { wch: 15 },
    ];
    ws["!cols"] = wscols;

    XLSX.utils.book_append_sheet(wb, ws, "Résultats RIB");

    // Add filter info to filename
    const filterSuffix =
      ibanFilter === "detected"
        ? "_IBAN_OK"
        : ibanFilter === "not-detected"
          ? "_IBAN_KO"
          : "";
    XLSX.writeFile(
      wb,
      `RIB_Export${filterSuffix}_${new Date().toISOString().slice(0, 10)}.xlsx`,
    );
  };

  // Filter function for items
  const getFilteredItems = () => {
    if (ibanFilter === "all") return items;

    return items.filter((item) => {
      const hasIban =
        item.response?.data?.iban && item.response.data.iban.length > 0;
      if (ibanFilter === "detected") return hasIban;
      if (ibanFilter === "not-detected")
        return !hasIban && item.status === "done";
      return true;
    });
  };

  const handleModalDelete = (id: string) => {
    const filteredItems = getFilteredItems();
    const currentIndex = filteredItems.findIndex((i) => i.id === id);

    // Deletion logic
    setItems((prev) => prev.filter((item) => item.id !== id));

    // Navigation logic: try next, then previous, then close
    if (filteredItems.length > 1) {
      if (currentIndex < filteredItems.length - 1) {
        setSelectedItemId(filteredItems[currentIndex + 1].id);
      } else if (currentIndex > 0) {
        // If it was the last item, go to the new last item
        setSelectedItemId(filteredItems[currentIndex - 1].id);
      } else {
        // If it was the only item, or the first and only remaining
        setSelectedItemId(null);
      }
    } else {
      setSelectedItemId(null);
    }
  };

  const handleNext = () => {
    const filteredItems = getFilteredItems();
    const currentIndex = filteredItems.findIndex(
      (i) => i.id === selectedItemId,
    );
    if (currentIndex !== -1 && currentIndex < filteredItems.length - 1) {
      setSelectedItemId(filteredItems[currentIndex + 1].id);
    }
  };

  const handlePrevious = () => {
    const filteredItems = getFilteredItems();
    const currentIndex = filteredItems.findIndex(
      (i) => i.id === selectedItemId,
    );
    if (currentIndex > 0) {
      setSelectedItemId(filteredItems[currentIndex - 1].id);
    }
  };

  const hasResults = items.length > 0;
  const completedCount = items.filter(
    (i) => i.status === "done" || i.status === "error",
  ).length;

  const filteredItems = getFilteredItems();
  const selectedItem = items.find((i) => i.id === selectedItemId);
  const selectedFilteredIndex = filteredItems.findIndex(
    (i) => i.id === selectedItemId,
  );

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 text-gray-900 font-sans pb-20">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-blue-400 to-cyan-300 rounded-full blur-3xl opacity-20 -translate-y-1/2 translate-x-1/3 animate-pulse"></div>
        <div
          className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-gradient-to-tr from-purple-400 to-pink-300 rounded-full blur-3xl opacity-20 translate-y-1/3 -translate-x-1/3 animate-pulse"
          style={{ animationDelay: "1s" }}
        ></div>
        <div className="absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-gradient-to-r from-indigo-400 to-blue-300 rounded-full blur-3xl opacity-10 -translate-x-1/2 -translate-y-1/2"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-8 pt-8">
        <header className="flex items-center justify-between mb-12 animate-fade-in-down">
          <div className="flex items-center gap-4">
            <img
              src="/logo.png"
              alt="RIB Factory"
              className="w-16 h-16 object-contain"
            />
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                RIB Factory
              </h1>
              <p className="text-sm text-gray-600 font-medium">
                Extraction de masse (OCR) - v1.1
              </p>
            </div>
          </div>

          <a
            href="https://github.com/jerome00253/RIB_Factory"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-white/50 hover:bg-white backdrop-blur-sm border border-gray-200 rounded-xl text-gray-700 hover:text-blue-600 transition-all shadow-sm hover:shadow-md group"
          >
            <Icon
              icon="mdi:github"
              className="w-6 h-6 group-hover:scale-110 transition-transform"
            />
            <span className="text-sm font-semibold">GitHub</span>
          </a>
        </header>

        <div className="space-y-8 animate-fade-in-up">
          {!hasResults ? (
            <div className="max-w-2xl mx-auto mt-20">
              <div className="text-center mb-10">
                <h2 className="text-4xl font-extrabold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-4">
                  Traitement par Lot
                </h2>
                <p className="text-gray-600 text-lg max-w-xl mx-auto leading-relaxed">
                  Importez jusqu'à{" "}
                  <span className="font-semibold text-blue-600">
                    24 fichiers
                  </span>{" "}
                  (PDF ou Images) simultanément. Notre moteur les traitera un
                  par un pour garantir la stabilité.
                </p>
              </div>
              <div className="bg-white/60 backdrop-blur-sm p-3 rounded-3xl shadow-xl border border-white/20">
                <UploadZone
                  onFileSelect={handleFilesSelect}
                  isProcessing={isProcessing}
                />
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
                  {/* Add Files Button */}
                  {!isProcessing && (
                    <label className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm cursor-pointer">
                      <Icon icon="mdi:plus" className="w-4 h-4" />
                      Ajouter au lot
                      <input
                        type="file"
                        className="hidden"
                        onChange={(e) => {
                          if (e.target.files && e.target.files.length > 0) {
                            handleFilesSelect(Array.from(e.target.files));
                            e.target.value = ""; // Reset input
                          }
                        }}
                        accept="image/*,application/pdf"
                        multiple
                      />
                    </label>
                  )}

                  {/* Export Button */}
                  <button
                    onClick={handleExport}
                    disabled={completedCount === 0}
                    className="px-4 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Icon
                      icon="mdi:microsoft-excel"
                      className="w-4 h-4 text-green-600"
                    />
                    Exporter Excel
                  </button>

                  {/* Delete Non-Detected Button */}
                  <button
                    onClick={handleDeleteNonDetected}
                    disabled={
                      items.filter(
                        (item) =>
                          item.status === "done" && !item.response?.data?.iban,
                      ).length === 0
                    }
                    className="px-4 py-2 bg-orange-50 border border-orange-200 hover:bg-orange-100 text-orange-700 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Icon icon="mdi:delete-alert" className="w-4 h-4" />
                    Supprimer non détectés
                  </button>

                  {/* Delete All Button */}
                  <button
                    onClick={handleDeleteAll}
                    disabled={items.length === 0}
                    className="px-4 py-2 bg-red-50 border border-red-200 hover:bg-red-100 text-red-700 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Icon icon="mdi:delete-sweep" className="w-4 h-4" />
                    Tout supprimer
                  </button>
                </div>
              </div>

              {/* Filter Controls - Separate Row */}
              <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <Icon icon="mdi:filter" className="w-5 h-5 text-gray-600" />
                  <span className="text-sm font-medium text-gray-700">
                    Filtrer :
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setIbanFilter("detected")}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        ibanFilter === "detected"
                          ? "bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-md"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      }`}
                    >
                      <Icon
                        icon="mdi:check-circle"
                        className="w-4 h-4 inline mr-1"
                      />
                      IBAN détecté
                    </button>
                    <button
                      onClick={() => setIbanFilter("not-detected")}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        ibanFilter === "not-detected"
                          ? "bg-gradient-to-r from-orange-600 to-red-600 text-white shadow-md"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      }`}
                    >
                      <Icon
                        icon="mdi:alert-circle"
                        className="w-4 h-4 inline mr-1"
                      />
                      IBAN non détecté
                    </button>
                    <button
                      onClick={() => setIbanFilter("all")}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        ibanFilter === "all"
                          ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      }`}
                    >
                      <Icon
                        icon="mdi:format-list-bulleted"
                        className="w-4 h-4 inline mr-1"
                      />
                      Tous
                    </button>
                  </div>
                  <div className="ml-auto text-sm text-gray-500">
                    {filteredItems.length} / {items.length} résultat(s)
                  </div>
                </div>
              </div>

              <RibTable
                results={filteredItems}
                onShowDetail={(filteredIndex) => {
                  setSelectedItemId(filteredItems[filteredIndex].id);
                }}
                onDelete={(filteredIndex) => {
                  handleDelete(
                    items.findIndex(
                      (i) => i.id === filteredItems[filteredIndex].id,
                    ),
                  );
                }}
              />
            </div>
          )}
        </div>
      </div>

      <footer className="fixed bottom-0 left-0 right-0 bg-white/70 backdrop-blur-sm border-t border-gray-200 text-center py-3 text-xs text-gray-600 z-50">
        <p>
          © 2026 @jerome0025 | Licence:{" "}
          <a
            href="https://www.gnu.org/licenses/gpl-3.0.html"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline font-semibold"
          >
            GNU GPL v3 (Copyleft)
          </a>
          {" "}|{" "}
          <a
            href="mailto:jerome0025@gmail.com"
            className="text-blue-600 hover:underline font-semibold"
          >
            Contact
          </a>
        </p>
      </footer>

      {selectedItemId && selectedItem && (
        <RibDetailModal
          file={selectedItem.file}
          result={selectedItem.response}
          onClose={() => setSelectedItemId(null)}
          onNext={
            selectedFilteredIndex < filteredItems.length - 1
              ? handleNext
              : undefined
          }
          onPrevious={selectedFilteredIndex > 0 ? handlePrevious : undefined}
          onDelete={() => handleModalDelete(selectedItemId)}
        />
      )}
    </main>
  );
}
