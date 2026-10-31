import React, { useEffect } from 'react';
import {
  Layers,
  CheckCircle2,
  Trash2,
  Eye,
  Power,
  RefreshCw,
  Clock,
  Sparkles,
} from 'lucide-react';
import { useClassifierStore } from '../../store/classifierStore';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

export const ModelRegistryTable: React.FC = () => {
  const {
    models,
    activeModel,
    selectedModel,
    actionLoading,
    fetchModels,
    fetchActiveModel,
    activateModel,
    deactivateModel,
    deleteModel,
    selectModelForInspection,
  } = useClassifierStore();

  useEffect(() => {
    fetchModels();
    fetchActiveModel();
  }, [fetchModels, fetchActiveModel]);

  return (
    <Card className="p-5 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-[rgba(148,180,210,0.12)]">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#48DDF5]" />
            <h3 className="text-base font-bold text-white tracking-wide">
              Module E: Model Registry &amp; Lifecycle Management
            </h3>
            <Badge variant="cyan">{models.length} Checkpoints</Badge>
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Version-controlled MLP weights (`.npz`) and metadata stored in `backend/models/classifiers/`. Hot-reload models into live camera stream without restarting backend.
          </p>
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            fetchModels();
            fetchActiveModel();
          }}
          className="text-xs flex items-center gap-1.5 border-[rgba(72,221,245,0.3)] text-[#48DDF5] hover:bg-[#48DDF5]/10 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Registry
        </Button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-[rgba(148,180,210,0.12)] bg-[#090E17]">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-[#111928] text-[#91A4B8] font-semibold border-b border-[rgba(148,180,210,0.12)]">
              <th className="py-2.5 px-3">Model Name / ID</th>
              <th className="py-2.5 px-3">Version</th>
              <th className="py-2.5 px-3">Classes</th>
              <th className="py-2.5 px-3">Test Acc</th>
              <th className="py-2.5 px-3">Created</th>
              <th className="py-2.5 px-3">Inference Status</th>
              <th className="py-2.5 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[rgba(148,180,210,0.06)]">
            {models.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-[#91A4B8]">
                  No trained models registered yet. Run training to create your first model checkpoint.
                </td>
              </tr>
            )}
            {models.map((m) => {
              const isActive = m.is_active || activeModel?.model_id === m.model_id;
              const isSelected = selectedModel?.model_id === m.model_id;
              const isActivating = actionLoading === `activate_${m.model_id}`;
              const isDeactivating = actionLoading === `deactivate_${m.model_id}`;
              const isDeleting = actionLoading === `delete_${m.model_id}`;

              return (
                <tr
                  key={m.model_id}
                  className={`hover:bg-white/[0.02] transition-colors ${
                    isSelected ? 'bg-[#00E5FF]/[0.04]' : ''
                  }`}
                >
                  <td className="py-2.5 px-3">
                    <div className="font-semibold text-white">{m.model_name}</div>
                    <div className="text-[10px] font-mono text-[#6B7280]">{m.model_id}</div>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[#91A4B8]">{m.version}</td>
                  <td className="py-2.5 px-3 font-mono text-white">
                    {m.classes.length} classes
                  </td>
                  <td className="py-2.5 px-3 font-mono font-semibold text-[#10B981]">
                    {(m.metrics.accuracy * 100).toFixed(1)}%
                  </td>
                  <td className="py-2.5 px-3 text-[#91A4B8] text-[11px] whitespace-nowrap">
                    {new Date(m.created_at).toLocaleDateString()} {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="py-2.5 px-3">
                    {isActive ? (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
                        ACTIVE
                      </span>
                    ) : (
                      <span className="text-[11px] text-[#6B7280]">Standby</span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {/* Inspect Button */}
                      <button
                        onClick={() => selectModelForInspection(m)}
                        className={`p-1.5 rounded-lg border text-xs transition-colors flex items-center gap-1 ${
                          isSelected
                            ? 'bg-[#00E5FF]/20 border-[#00E5FF] text-[#00E5FF]'
                            : 'bg-white/5 border-[rgba(148,180,210,0.15)] text-[#91A4B8] hover:text-white'
                        }`}
                        title="Inspect Evaluation Metrics"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Inspect</span>
                      </button>

                      {/* Activate / Deactivate Button */}
                      {isActive ? (
                        <button
                          onClick={() => deactivateModel(m.model_id)}
                          disabled={isDeactivating}
                          className="p-1.5 px-2.5 rounded-lg border border-[#F59E0B]/30 bg-[#F59E0B]/10 text-[#F59E0B] hover:bg-[#F59E0B]/20 text-xs transition-colors flex items-center gap-1"
                          title="Deactivate Model"
                        >
                          <Power className={`w-3.5 h-3.5 ${isDeactivating ? 'animate-spin' : ''}`} />
                          <span className="hidden sm:inline">Deactivate</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => activateModel(m.model_id)}
                          disabled={isActivating}
                          className="p-1.5 px-2.5 rounded-lg border border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981] hover:bg-[#10B981]/20 text-xs transition-colors flex items-center gap-1 font-medium"
                          title="Activate for Real-time Inference"
                        >
                          <Power className={`w-3.5 h-3.5 ${isActivating ? 'animate-spin' : ''}`} />
                          <span className="hidden sm:inline">Activate</span>
                        </button>
                      )}

                      {/* Delete Button */}
                      <button
                        onClick={() => {
                          if (window.confirm(`Delete model checkpoint "${m.model_name}"?`)) {
                            deleteModel(m.model_id);
                          }
                        }}
                        disabled={isDeleting}
                        className="p-1.5 rounded-lg border border-[#EF4444]/20 bg-[#EF4444]/5 text-[#EF4444] hover:bg-[#EF4444]/20 text-xs transition-colors"
                        title="Delete Model"
                      >
                        <Trash2 className={`w-3.5 h-3.5 ${isDeleting ? 'animate-spin' : ''}`} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
