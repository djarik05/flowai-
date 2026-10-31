import React from 'react';
import { Award, BarChart3, CheckCircle2, Table, Layers, Info } from 'lucide-react';
import { useClassifierStore } from '../../store/classifierStore';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const EvaluationDashboard: React.FC = () => {
  const { selectedModel, activeModel } = useClassifierStore();

  const model = selectedModel || activeModel;

  if (!model) {
    return (
      <Card className="p-6 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
        <div className="flex items-center gap-2 mb-2">
          <Award className="w-5 h-5 text-[#48DDF5]" />
          <h3 className="text-base font-bold text-white tracking-wide">
            Module D: Evaluation &amp; Confusion Matrix
          </h3>
        </div>
        <div className="py-10 text-center text-[#91A4B8] text-xs">
          No trained model selected. Complete a training run or select a model from the Model Registry below to inspect test set metrics and confusion matrix.
        </div>
      </Card>
    );
  }

  const metrics = model.metrics;
  const labels = metrics.class_labels || [];
  const cm = metrics.confusion_matrix || [];
  const perClass = metrics.per_class || {};

  return (
    <Card className="p-5 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-[rgba(148,180,210,0.12)]">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-[#48DDF5]" />
            <h3 className="text-base font-bold text-white tracking-wide">
              Module D: Independent Test Set Evaluation
            </h3>
            {model.is_active && <Badge variant="green">Active in Live Inference</Badge>}
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Model: <strong className="text-white">{model.model_name}</strong> ({model.model_id}) &bull; Feature: {model.feature_dim}-D ({model.feature_schema})
          </p>
        </div>

        <div className="text-xs text-[#91A4B8] font-mono">
          Evaluated on <strong className="text-[#00E5FF]">{metrics.test_samples_count}</strong> holdout test samples
        </div>
      </div>

      {/* Macro Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Test Accuracy
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-[#10B981]">
              {(metrics.accuracy * 100).toFixed(1)}%
            </span>
          </div>
          <span className="text-[10px] text-[#91A4B8] mt-0.5 block">Overall holdout score</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Macro Precision
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-[#00E5FF]">
              {(metrics.precision_macro * 100).toFixed(1)}%
            </span>
          </div>
          <span className="text-[10px] text-[#91A4B8] mt-0.5 block">Avg class precision</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Macro Recall
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-[#38BDF8]">
              {(metrics.recall_macro * 100).toFixed(1)}%
            </span>
          </div>
          <span className="text-[10px] text-[#91A4B8] mt-0.5 block">Avg class sensitivity</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Macro F1-Score
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-[#A855F7]">
              {(metrics.f1_macro * 100).toFixed(1)}%
            </span>
          </div>
          <span className="text-[10px] text-[#91A4B8] mt-0.5 block">Harmonic mean</span>
        </div>
      </div>

      {/* Two Columns: Confusion Matrix & Per-Class Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Confusion Matrix */}
        <div className="p-4 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-1.5">
              <BarChart3 className="w-4 h-4 text-[#00E5FF]" />
              <span className="text-xs font-bold text-white tracking-wide">
                Confusion Matrix (True vs Predicted)
              </span>
            </div>
            <span className="text-[10px] text-[#6B7280]">Diagonal = Correct</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-center text-xs border-collapse">
              <thead>
                <tr>
                  <th className="p-1 text-[10px] text-[#6B7280] text-left font-normal">True \ Pred</th>
                  {labels.map((lbl, idx) => (
                    <th
                      key={idx}
                      className="p-1 text-[11px] font-mono text-[#00E5FF] font-semibold max-w-[70px] truncate"
                      title={lbl}
                    >
                      {lbl.length > 8 ? lbl.substring(0, 7) + '…' : lbl}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cm.map((row, rowIdx) => {
                  const trueLabel = labels[rowIdx] || `Class ${rowIdx}`;
                  return (
                    <tr key={rowIdx}>
                      <td
                        className="p-1 text-[11px] font-mono text-[#91A4B8] text-left font-medium max-w-[80px] truncate"
                        title={trueLabel}
                      >
                        {trueLabel.length > 9 ? trueLabel.substring(0, 8) + '…' : trueLabel}
                      </td>
                      {row.map((val, colIdx) => {
                        const isDiagonal = rowIdx === colIdx;
                        const isCorrect = isDiagonal && val > 0;
                        const isError = !isDiagonal && val > 0;

                        return (
                          <td
                            key={colIdx}
                            className={`p-2 border border-[rgba(148,180,210,0.06)] font-mono text-xs font-bold transition-all ${
                              isCorrect
                                ? 'bg-[#10B981]/25 text-[#10B981]'
                                : isError
                                ? 'bg-[#EF4444]/25 text-[#EF4444]'
                                : val === 0
                                ? 'bg-[#090E17] text-[#4B5563]'
                                : 'bg-white/5 text-white'
                            }`}
                          >
                            {val}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Per-Class Breakdown Table */}
        <div className="p-4 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-1.5">
              <Table className="w-4 h-4 text-[#00E5FF]" />
              <span className="text-xs font-bold text-white tracking-wide">
                Per-Class Performance
              </span>
            </div>
            <span className="text-[10px] text-[#6B7280]">{Object.keys(perClass).length} classes</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[rgba(148,180,210,0.12)] text-[#91A4B8]">
                  <th className="py-1.5 px-2">Class</th>
                  <th className="py-1.5 px-2 text-right">Precision</th>
                  <th className="py-1.5 px-2 text-right">Recall</th>
                  <th className="py-1.5 px-2 text-right">F1-Score</th>
                  <th className="py-1.5 px-2 text-right">Support</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[rgba(148,180,210,0.06)] font-mono">
                {Object.entries(perClass).map(([clsName, m]) => (
                  <tr key={clsName} className="hover:bg-white/[0.02]">
                    <td className="py-2 px-2 text-white font-sans font-medium">{clsName}</td>
                    <td className="py-2 px-2 text-right text-[#00E5FF]">
                      {(m.precision * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 px-2 text-right text-[#38BDF8]">
                      {(m.recall * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 px-2 text-right text-[#A855F7] font-semibold">
                      {(m.f1_score * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 px-2 text-right text-[#91A4B8]">{m.support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Card>
  );
};
