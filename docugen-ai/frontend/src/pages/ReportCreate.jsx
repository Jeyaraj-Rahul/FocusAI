import { Download, Image, Wand2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import Button from "../components/common/Button.jsx";
import Card from "../components/common/Card.jsx";
import Field from "../components/common/Field.jsx";
import LoadingSpinner from "../components/common/LoadingSpinner.jsx";
import Dropzone from "../components/upload/Dropzone.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { generateDocx, generatePdf, listImages, uploadReportImage } from "../services/reportService.js";
import { listTemplates } from "../services/templateService.js";
import { getErrorMessage } from "../utils/errors.js";

export default function ReportCreate() {
  const { showToast } = useToast();
  const [templates, setTemplates] = useState([]);
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [generating, setGenerating] = useState("");
  const [imageMeta, setImageMeta] = useState({ caption: "", sectionHeading: "Implementation" });
  const [form, setForm] = useState({
    title: "My Project Report",
    subtitle: "",
    author_name: "",
    institution: "",
    template_id: "",
    section_heading: "Introduction",
    content: "Write your project notes here. The generated document will include this text as a report paragraph."
  });

  const selectedImageIds = useMemo(() => images.map((image) => image.id), [images]);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [templateData, imageData] = await Promise.all([listTemplates(), listImages()]);
        setTemplates(templateData);
        setImages(imageData);
      } catch (error) {
        showToast({ type: "error", title: "Could not load report data", message: getErrorMessage(error) });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  async function handleImageFiles(files) {
    const [file] = files;
    if (!file) return;
    setUploadingImage(true);
    try {
      const image = await uploadReportImage({
        file,
        caption: imageMeta.caption || file.name,
        sectionHeading: imageMeta.sectionHeading
      });
      setImages((items) => [image, ...items]);
      showToast({ type: "success", title: "Image uploaded", message: "It will be inserted into the matching report section." });
    } catch (error) {
      showToast({ type: "error", title: "Image upload failed", message: getErrorMessage(error) });
    } finally {
      setUploadingImage(false);
    }
  }

  function reportPayload() {
    return {
      title: form.title,
      subtitle: form.subtitle || null,
      author_name: form.author_name || null,
      institution: form.institution || null,
      template_id: form.template_id ? Number(form.template_id) : null,
      image_ids: selectedImageIds,
      sections: [
        {
          heading: form.section_heading || "Introduction",
          paragraphs: [form.content]
        }
      ]
    };
  }

  async function handleGenerate(type) {
    if (!form.title.trim() || !form.content.trim()) {
      showToast({ type: "error", title: "Missing report content", message: "Add a title and report paragraph before exporting." });
      return;
    }
    setGenerating(type);
    try {
      const filename = type === "docx" ? await generateDocx(reportPayload()) : await generatePdf(reportPayload());
      showToast({ type: "success", title: "Download ready", message: `${filename} has been downloaded.` });
    } catch (error) {
      showToast({ type: "error", title: "Export failed", message: getErrorMessage(error) });
    } finally {
      setGenerating("");
    }
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[1fr_380px]">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-950 dark:text-white">Create Report</h2>
          <p className="mt-2 text-slate-600 dark:text-slate-400">Enter report content, upload screenshots, then export DOCX or PDF from the backend.</p>
        </div>

        <Card className="space-y-4 p-5">
          <Field label="Report title">
            <input className="w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
          </Field>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Subtitle">
              <input className="w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={form.subtitle} onChange={(event) => setForm({ ...form, subtitle: event.target.value })} />
            </Field>
            <Field label="Template">
              <select className="w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={form.template_id} onChange={(event) => setForm({ ...form, template_id: event.target.value })}>
                <option value="">Default formatting</option>
                {templates.map((template) => <option key={template.id} value={template.id}>{template.name}</option>)}
              </select>
            </Field>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Author name">
              <input className="w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={form.author_name} onChange={(event) => setForm({ ...form, author_name: event.target.value })} />
            </Field>
            <Field label="Institution">
              <input className="w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={form.institution} onChange={(event) => setForm({ ...form, institution: event.target.value })} />
            </Field>
          </div>
          <Field label="Section heading">
            <input className="w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={form.section_heading} onChange={(event) => setForm({ ...form, section_heading: event.target.value, })} />
          </Field>
          <Field label="Report paragraph">
            <textarea className="min-h-40 w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={form.content} onChange={(event) => setForm({ ...form, content: event.target.value })} />
          </Field>
        </Card>
      </div>

      <aside className="space-y-6">
        <Card className="space-y-4 p-5">
          <h3 className="font-semibold text-slate-950 dark:text-white">Upload screenshot/photo</h3>
          <Field label="Caption">
            <input className="w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={imageMeta.caption} onChange={(event) => setImageMeta({ ...imageMeta, caption: event.target.value })} />
          </Field>
          <Field label="Target section">
            <input className="w-full rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white" value={imageMeta.sectionHeading} onChange={(event) => setImageMeta({ ...imageMeta, sectionHeading: event.target.value })} />
          </Field>
          <Dropzone accept="image/png,image/jpeg,image/jpg,image/bmp,image/gif" label={uploadingImage ? "Uploading image..." : "Upload image"} hint="PNG, JPG, BMP, or GIF" disabled={uploadingImage} onFiles={handleImageFiles} />
        </Card>

        <Card className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-semibold text-slate-950 dark:text-white">Uploaded images</h3>
            {loading ? <LoadingSpinner label="Loading" /> : null}
          </div>
          <div className="space-y-3">
            {images.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">No images uploaded yet.</p>
            ) : images.map((image) => (
              <div key={image.id} className="flex items-center gap-3 rounded-md border border-slate-200 p-3 dark:border-slate-800">
                <Image className="h-5 w-5 text-blue-500" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium dark:text-white">{image.caption || image.original_filename}</p>
                  <p className="text-xs text-slate-500">{image.section_heading || "Final section"} - {image.width_px}x{image.height_px}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="space-y-3 p-5">
          <Button className="w-full" onClick={() => handleGenerate("docx")} disabled={Boolean(generating)}>
            {generating === "docx" ? <LoadingSpinner label="Generating DOCX" /> : <><Download size={18} /> Download DOCX</>}
          </Button>
          <Button variant="secondary" className="w-full" onClick={() => handleGenerate("pdf")} disabled={Boolean(generating)}>
            {generating === "pdf" ? <LoadingSpinner label="Generating PDF" /> : <><Wand2 size={18} /> Download PDF</>}
          </Button>
        </Card>
      </aside>
    </section>
  );
}
