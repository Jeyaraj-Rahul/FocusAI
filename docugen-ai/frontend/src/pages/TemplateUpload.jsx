import { FileText } from "lucide-react";
import { useEffect, useState } from "react";
import Card from "../components/common/Card.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import LoadingSpinner from "../components/common/LoadingSpinner.jsx";
import Dropzone from "../components/upload/Dropzone.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { getErrorMessage } from "../utils/errors.js";
import { listTemplates, uploadTemplate } from "../services/templateService.js";

export default function TemplateUpload() {
  const { showToast } = useToast();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  async function loadTemplates() {
    setLoading(true);
    try {
      setTemplates(await listTemplates());
    } catch (error) {
      showToast({ type: "error", title: "Could not load templates", message: getErrorMessage(error) });
    } finally {
      setLoading(false);
    }
  }

  async function handleFiles(files) {
    const [file] = files;
    if (!file) return;
    setUploading(true);
    try {
      const template = await uploadTemplate(file);
      setTemplates((items) => [template, ...items]);
      showToast({ type: "success", title: "Template uploaded", message: `${template.name} is ready to use.` });
    } catch (error) {
      showToast({ type: "error", title: "Upload failed", message: getErrorMessage(error) });
    } finally {
      setUploading(false);
    }
  }

  useEffect(() => {
    loadTemplates();
  }, []);

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-950 dark:text-white">Template Upload</h2>
        <p className="mt-2 text-slate-600 dark:text-slate-400">Upload a DOCX sample report to extract margins, heading styles, fonts, spacing, and table rules.</p>
      </div>

      <Card className="p-5">
        <Dropzone
          accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          label={uploading ? "Uploading template..." : "Upload DOCX template"}
          hint="Drag a .docx file here or click to browse"
          disabled={uploading}
          onFiles={handleFiles}
        />
      </Card>

      <Card className="p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-semibold text-slate-950 dark:text-white">Saved formatting profiles</h3>
          {loading ? <LoadingSpinner label="Loading" /> : null}
        </div>

        {!loading && templates.length === 0 ? (
          <EmptyState icon={<FileText size={22} />} title="No templates uploaded" description="Upload a DOCX template to reuse its formatting during report generation." />
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            {templates.map((template) => (
              <article key={template.id} className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                <p className="font-semibold text-slate-950 dark:text-white">{template.name}</p>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{template.original_filename}</p>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="text-slate-500">Font</dt>
                    <dd className="font-medium dark:text-slate-200">{template.profile?.formatting_options?.font_family || "Detected"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Line spacing</dt>
                    <dd className="font-medium dark:text-slate-200">{template.profile?.formatting_options?.line_spacing || "Auto"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Heading styles</dt>
                    <dd className="font-medium dark:text-slate-200">{template.profile?.heading_styles?.length || 0}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Tables</dt>
                    <dd className="font-medium dark:text-slate-200">{template.profile?.table_styles?.length || 0}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        )}
      </Card>
    </section>
  );
}
