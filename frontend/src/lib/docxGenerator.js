import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';

/**
 * Generates a structurally valid OOXML Word Document (.docx) Blob in the browser
 * using the `docx` library. This produces a true OpenXML ZIP archive that opens natively
 * in Microsoft Word without any "unreadable content" warnings.
 */
export async function generateDemoDocxBlob(metadata = {}) {
  const timestampStr = metadata.timestamp || new Date().toISOString();
  const docName = metadata.filename || 'MAINTENANCE_APPROVAL_NOTE_B102_DEMO.docx';

  const doc = new Document({
    creator: "VAJRA Sovereign AI Workbench",
    title: "Maintenance Approval Note #B-102",
    description: "Synthetic Demo Deliverable for SIH 2026 Public Showcase",
    sections: [
      {
        properties: {},
        children: [
          // Header / Subtitle
          new Paragraph({
            alignment: AlignmentType.LEFT,
            children: [
              new TextRun({
                text: "VAJRA — SOVEREIGN AI WORKBENCH",
                bold: true,
                size: 24, // 12pt
                color: "00838F" // Teal/Cyan accent
              })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({
                text: "(SYNTHETIC DEMO DELIVERABLE)",
                bold: true,
                italic: true,
                size: 18, // 9pt
                color: "D97706" // Amber badge accent
              })
            ]
          }),

          // Spacer
          new Paragraph({ text: "" }),

          // Document Title
          new Paragraph({
            children: [
              new TextRun({
                text: "MAINTENANCE APPROVAL NOTE #B-102",
                bold: true,
                size: 32, // 16pt
                color: "0F172A"
              })
            ]
          }),

          new Paragraph({ text: "" }),

          // Facility & Equipment ID
          new Paragraph({
            children: [
              new TextRun({ text: "FACILITY: ", bold: true, color: "334155" }),
              new TextRun({ text: "SRM/SIH Unit - Zone 4 High Pressure Loop" })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({ text: "EQUIPMENT ID: ", bold: true, color: "334155" }),
              new TextRun({ text: "Boiler Feedwater Pump B-102" })
            ]
          }),

          new Paragraph({ text: "" }),

          // Critical Finding Section
          new Paragraph({
            children: [
              new TextRun({ text: "CRITICAL FINDING:", bold: true, color: "DC2626" })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({
                text: "Measured drive-end bearing vibration reached 7.8 mm/s RMS, exceeding ISO 10816 Class II threshold (4.5 mm/s) & SOP limit (7.0 mm/s)."
              })
            ]
          }),

          new Paragraph({ text: "" }),

          // Recommended Action Section
          new Paragraph({
            children: [
              new TextRun({ text: "RECOMMENDED MAINTENANCE ACTION:", bold: true, color: "0F172A" })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({
                text: "Inspect drive-end bearing sleeve B-102-BRG and perform LOTO clearance on Valve HV-104."
              })
            ]
          }),

          new Paragraph({ text: "" }),

          // Governance & Approval Block
          new Paragraph({
            children: [
              new TextRun({ text: "HUMAN GOVERNANCE SIGN-OFF", bold: true, size: 22, color: "0F172A" })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({ text: "STATUS: ", bold: true, color: "334155" }),
              new TextRun({ text: "APPROVED & SIGNED", bold: true, color: "059669" })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({ text: "REVIEWER: ", bold: true, color: "334155" }),
              new TextRun({ text: "Chief Maintenance Operations Lead" })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({ text: "TIMESTAMP: ", bold: true, color: "334155" }),
              new TextRun({ text: timestampStr })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({ text: "SECURITY POLICY: ", bold: true, color: "334155" }),
              new TextRun({ text: "Synthetic Demo Deliverable (Air-Gapped Architecture)" })
            ]
          })
        ]
      }
    ]
  });

  // Pack document to valid OOXML binary Blob
  const blob = await Packer.toBlob(doc);
  return blob;
}

/**
 * Triggers a browser download of the valid OOXML .docx Blob.
 */
export async function downloadDemoDocx(filename = 'MAINTENANCE_APPROVAL_NOTE_B102_DEMO.docx', metadata = {}) {
  const blob = await generateDemoDocxBlob(metadata);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
