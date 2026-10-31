import React, { useState } from 'react';
import {
  ShieldCheck,
  Download,
  AlertTriangle,
  CheckCircle2,
  FileSpreadsheet,
  FileCode,
  RefreshCw,
  Search,
  Sparkles,
  Info,
} from 'lucide-react';
import { useDatasetStore } from '../../../store/datasetStore';
import { DatasetApi } from '../../../services/api/dataset';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

export const ValidationExportTab: React.FC = () => {
  const { validationReport, isValidating, runValidation } = useDatasetStore();
  const [isExportingCsv, setIsExportingCsv] = useState(false);
  const [isExportingJson, setIsExportingJson] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleRunValidation = async () => {
    await runValidation();
  };

  const handleExportCsv = async () => {
    setIsExportingCsv(true);
    setExportError(null);
    try {
      await DatasetApi.downloadExport('csv');
    } catch (err: any) {
      setExportError(err?.message || 'Failed to download CSV export');
    } finally {
      setIsExportingCsv(false);
    }
  };

  const handleExportJson = async () => {
    setIsExportingJson(true);
    setExportError(null);
    try {
      await DatasetApi.downloadExport('json');
    } catch (err: any) {
      setExportError(err?.message || 'Failed to download JSON export');
    } finally {
      setIsExportingJson(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Top Banner: Export Downloads */}
      <Card variant="glass" className="p-5 flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Download className="w-4 h-4 text-[#48DDF5]" />
              Dataset Export Center
            </h3>
            <p className="text-xs text-[#91A4B8] mt-0.5">
              Download your complete hand landmark dataset for machine learning model training or archival.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportCsv}
              disabled={isExportingCsv}
              icon={<FileSpreadsheet className="w-4 h-4 text-[#42F5A5]" />}
              className="text-xs"
            >
              {isExportingCsv ? 'Exporting...' : 'Download CSV (ML Ready)'}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleExportJson}
              disabled={isExportingJson}
              icon={<FileCode className="w-4 h-4 text-[#48DDF5]" />}
              className="text-xs"
            >
              {isExportingJson ? 'Exporting...' : 'Download JSON Archive'}
            </Button>
          </div>
        </div>

        {exportError && (
          <div className="p-3 rounded-lg bg-[rgba(255,100,124,0.12)] border border-[rgba(255,100,124,0.3)] text-xs text-[#FF647C]">
            {exportError}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-[rgba(148,180,210,0.1)] text-xs font-mono">
          <div className="p-3 rounded-xl bg-[rgba(11,18,32,0.5)] border border-[rgba(148,180,210,0.08)]">
            <span className="text-[#42F5A5] font-bold block mb-1 flex items-center gap-1.5">
              <FileSpreadsheet className="w-3.5 h-3.5" />
              Flattened CSV Format
            </span>
            <p className="text-[#91A4B8] text-[11px] font-sans">
              Contains metadata columns plus flattened 63 coordinates (<code className="text-[#48DDF5]">x_0, y_0, z_0 ... x_20, y_20, z_20</code>). Directly compatible with Scikit-Learn, PyTorch and Random Forest classifiers.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-[rgba(11,18,32,0.5)] border border-[rgba(148,180,210,0.08)]">
            <span className="text-[#48DDF5] font-bold block mb-1 flex items-center gap-1.5">
              <FileCode className="w-3.5 h-3.5" />
              Structured JSON Format
            </span>
            <p className="text-[#91A4B8] text-[11px] font-sans">
              Contains complete gesture registry metadata, session hierarchies, and preserved original MediaPipe landmark arrays with timestamp and confidence records.
            </p>
          </div>
        </div>
      </Card>

      {/* Dataset Validation Section */}
      <Card variant="glass" className="p-5 flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#42F5A5]" />
              Dataset Quality &amp; Integrity Audit
            </h3>
            <p className="text-xs text-[#91A4B8] mt-0.5">
              Performs exhaustive integrity scans to detect missing coordinates, corrupted JSON files, duplicate sample IDs, or invalid handedness tags.
            </p>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={handleRunValidation}
            disabled={isValidating}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isValidating ? 'animate-spin' : ''}`} />}
            className="text-xs"
          >
            {isValidating ? 'Running Audit...' : 'Run Validation Audit'}
          </Button>
        </div>

        {/* Validation Report Details */}
        {validationReport ? (
          <div className="flex flex-col gap-4 pt-2">
            {/* Status Summary Banner */}
            <div
              className={`p-4 rounded-xl border flex flex-wrap items-center justify-between gap-3 ${
                validationReport.is_valid
                  ? 'bg-[rgba(66,245,165,0.08)] border-[rgba(66,245,165,0.25)] text-[#42F5A5]'
                  : 'bg-[rgba(255,181,71,0.08)] border-[rgba(255,181,71,0.25)] text-[#FFB547]'
              }`}
            >
              <div className="flex items-center gap-3">
                {validationReport.is_valid ? (
                  <CheckCircle2 className="w-6 h-6 text-[#42F5A5]" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-[#FFB547]" />
                )}
                <div>
                  <h4 className="font-bold text-white text-sm">
                    {validationReport.is_valid
                      ? 'Dataset Passed All Validation Checks'
                      : `Validation Found ${validationReport.issues_count} Potential Issues`}
                  </h4>
                  <p className="text-xs text-[#91A4B8] mt-0.5 font-mono">
                    Audit evaluated {validationReport.total_checked} samples at{' '}
                    {new Date(validationReport.checked_at).toLocaleTimeString()}.
                  </p>
                </div>
              </div>

              <Badge variant={validationReport.is_valid ? 'green' : 'warning'}>
                {validationReport.is_valid ? '100% Valid' : 'Audit Warnings'}
              </Badge>
            </div>

            {/* Issues List if any */}
            {validationReport.issues.length > 0 && (
              <div className="overflow-x-auto rounded-xl border border-[rgba(148,180,210,0.14)]">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#0B1220] border-b border-[rgba(148,180,210,0.14)] text-[10px] uppercase text-[#91A4B8]">
                    <tr>
                      <th className="py-2.5 px-3">Severity</th>
                      <th className="py-2.5 px-3">Sample ID</th>
                      <th className="py-2.5 px-3">Gesture ID</th>
                      <th className="py-2.5 px-3">Issue Type</th>
                      <th className="py-2.5 px-3">Detail</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[rgba(148,180,210,0.08)]">
                    {validationReport.issues.map((issue, idx) => (
                      <tr key={idx} className="hover:bg-[rgba(255,100,124,0.04)]">
                        <td className="py-2 px-3">
                          <Badge variant={issue.severity === 'error' ? 'error' : 'warning'}>
                            {issue.severity}
                          </Badge>
                        </td>
                        <td className="py-2 px-3 text-white font-bold">{issue.sample_id}</td>
                        <td className="py-2 px-3 text-[#48DDF5]">{issue.gesture_id}</td>
                        <td className="py-2 px-3">{issue.issue_type}</td>
                        <td className="py-2 px-3 text-[#91A4B8]">{issue.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 rounded-xl bg-[rgba(11,18,32,0.4)] border border-dashed border-[rgba(148,180,210,0.15)] flex flex-col items-center justify-center text-center">
            <ShieldCheck className="w-8 h-8 text-[#91A4B8] mb-2 opacity-60" />
            <h5 className="text-xs font-semibold text-white">No validation audit run yet</h5>
            <p className="text-[11px] text-[#91A4B8] mt-1 max-w-sm mb-3">
              Click &quot;Run Validation Audit&quot; above to verify all collected samples against missing coordinates, format corruption, and integrity checks.
            </p>
            <Button variant="outline" size="sm" onClick={handleRunValidation}>
              Start Audit Now
            </Button>
          </div>
        )}

        {/* Audit Coverage Description */}
        <div className="p-3.5 rounded-xl bg-[rgba(11,18,32,0.4)] border border-[rgba(148,180,210,0.1)] text-xs text-[#91A4B8]">
          <span className="text-[#F1F5F9] font-semibold block mb-1.5 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-[#48DDF5]" />
            Validation Rules Enforced
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-[11px] font-mono">
            <div>✓ Exactly 21 coordinates per sample</div>
            <div>✓ Coordinate bounds [0.0, 1.0]</div>
            <div>✓ Valid JSON syntax parsing</div>
            <div>✓ Handedness verification</div>
            <div>✓ Unique sample ID enforcement</div>
            <div>✓ Gesture registry ID alignment</div>
          </div>
        </div>
      </Card>
    </div>
  );
};
