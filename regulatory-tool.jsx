import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════
// REGULATORY KNOWLEDGE BASE
// ═══════════════════════════════════════════════════════════════

const MARKETS = {
  US: { name: "United States", agency: "FDA", flag: "🇺🇸", color: "#1a4480" },
  EU: { name: "European Union", agency: "EU MDR", flag: "🇪🇺", color: "#003399" },
  UK: { name: "United Kingdom", agency: "MHRA", flag: "🇬🇧", color: "#c8102e" },
  BR: { name: "Brazil", agency: "ANVISA", flag: "🇧🇷", color: "#009c3b" },
  MX: { name: "Mexico", agency: "COFEPRIS", flag: "🇲🇽", color: "#006847" },
  CO: { name: "Colombia", agency: "INVIMA", flag: "🇨🇴", color: "#fcd116" },
  AR: { name: "Argentina", agency: "ANMAT", flag: "🇦🇷", color: "#74acdf" },
};

const DEVICE_CLASSIFICATIONS = {
  US: {
    "Class I": {
      description: "Low risk devices, most exempt from 510(k)",
      pathway: "510(k) exempt (most); some require 510(k)",
      qsr: "21 CFR 820 (abbreviated for exempt devices)",
      timeline: "N/A for exempt; 3-6 months for 510(k)",
      establishment: "Establishment Registration + Device Listing required",
      fees: "Annual establishment registration fee (~$7,653/yr FY2025)",
    },
    "Class II": {
      description: "Moderate risk devices, most require 510(k)",
      pathway: "510(k) Premarket Notification (most common); De Novo for novel devices",
      qsr: "Full 21 CFR 820 Quality System Regulation compliance",
      timeline: "510(k): 3-12 months; De Novo: 6-18 months",
      establishment: "Establishment Registration + Device Listing required",
      fees: "510(k) review fee (~$22,124 FY2025 for small business; ~$88,495 standard)",
    },
  },
  EU: {
    "Class I": {
      description: "Low risk, self-declaration with Notified Body for sterile/measuring",
      pathway: "Self-certification (Annex II & III); NB required if sterile, measuring, or reusable surgical",
      qsr: "Full EU MDR 2017/745 Annex I Essential Requirements + ISO 13485 QMS",
      timeline: "6-12 months for technical documentation preparation",
      establishment: "Authorized Representative required; EUDAMED registration",
      fees: "Varies by Notified Body; AR fees €5,000-15,000/yr",
    },
    "Class IIa": {
      description: "Low-moderate risk, requires Notified Body certification",
      pathway: "Conformity assessment via Notified Body (Annex IX or XI)",
      qsr: "Full EU MDR 2017/745 compliance + ISO 13485 QMS + Technical Documentation per Annex II & III",
      timeline: "12-18 months including NB audit",
      establishment: "Authorized Representative required; EUDAMED registration; UDI-DI assignment",
      fees: "NB certification €15,000-50,000; annual surveillance €10,000-25,000",
    },
    "Class IIb": {
      description: "Medium-high risk, requires Notified Body with type examination",
      pathway: "Conformity assessment via Notified Body (Annex IX + Annex X for implantables)",
      qsr: "Full EU MDR 2017/745 + ISO 13485 + Clinical Evaluation per Annex XIV",
      timeline: "18-24+ months",
      establishment: "Authorized Representative required; EUDAMED registration; UDI-DI assignment",
      fees: "NB certification €30,000-80,000+; annual surveillance €15,000-40,000",
    },
  },
  UK: {
    "Class I": {
      description: "Low risk, self-declaration under UK MDR 2002 (as amended)",
      pathway: "Self-certification; UKCA marking (CE marking accepted until June 2030)",
      qsr: "UK MDR 2002 + ISO 13485 QMS",
      timeline: "3-6 months",
      establishment: "MHRA device registration required; UK Responsible Person if non-UK manufacturer",
      fees: "MHRA registration fees apply; UKRP fees vary",
    },
    "Class II": {
      description: "Moderate risk, requires UK Approved Body",
      pathway: "UKCA marking via UK Approved Body (CE accepted until June 2030 transition)",
      qsr: "UK MDR 2002 + ISO 13485 QMS + Essential Requirements",
      timeline: "12-18 months",
      establishment: "MHRA registration; UK Responsible Person required",
      fees: "Approved Body fees comparable to EU NB fees",
    },
  },
  BR: {
    "Class I": {
      description: "Low risk (Classe I under RDC 751/2022)",
      pathway: "Cadastro (notification/registration) via ANVISA",
      qsr: "RDC 665/2022 (GMP) + INMETRO certification for applicable products + Brazilian GMP (BGMP)",
      timeline: "3-6 months for Cadastro",
      establishment: "Brazilian Registration Holder (BRH) required; GMP certification",
      fees: "Registration fees ~R$4,000-8,000; GMP inspection fees additional",
    },
    "Class II": {
      description: "Moderate risk (Classe II under RDC 751/2022)",
      pathway: "Registro (full registration) via ANVISA",
      qsr: "RDC 665/2022 (GMP) + BGMP compliance + Technical documentation + Clinical evidence",
      timeline: "12-24 months for Registro",
      establishment: "Brazilian Registration Holder (BRH) required; GMP certification mandatory",
      fees: "Registration fees ~R$8,000-25,000; GMP audit fees R$15,000-50,000+",
    },
  },
  MX: {
    "Class I": {
      description: "Low risk under COFEPRIS classification",
      pathway: "Registro Sanitario (health registration) - simplified",
      qsr: "NOM-241-SSA1-2021 (GMP) compliance; ISO 13485 recognized",
      timeline: "3-6 months",
      establishment: "Legal representative in Mexico required; Sanitary License (Licencia Sanitaria)",
      fees: "Registration fees vary; legal representative costs $5,000-15,000/yr",
    },
    "Class II": {
      description: "Moderate risk under COFEPRIS classification",
      pathway: "Registro Sanitario with technical dossier review",
      qsr: "NOM-241-SSA1-2021 (GMP) + Technical dossier with safety/efficacy data",
      timeline: "6-18 months",
      establishment: "Legal representative; Sanitary License; GMP compliance certificate",
      fees: "Registration fees + technical review fees; third-party testing may be required",
    },
  },
  CO: {
    "Class I": {
      description: "Low risk (Clase I under Decreto 4725 de 2005)",
      pathway: "Registro Sanitario via INVIMA - automatic/simplified",
      qsr: "Decreto 4725 de 2005 + Resolución 4002 de 2007 (GMP/BPE)",
      timeline: "1-3 months for simplified registration",
      establishment: "Colombian legal representative or importer required",
      fees: "Registration fees ~COP 5-15 million",
    },
    "Class II": {
      description: "Moderate risk (Clase IIa/IIb)",
      pathway: "Registro Sanitario via INVIMA with technical evaluation",
      qsr: "Decreto 4725 + GMP/BPE compliance + Technical documentation review",
      timeline: "6-12 months",
      establishment: "Colombian legal representative; Certificate of Free Sale from origin country",
      fees: "Registration fees ~COP 15-40 million; evaluation fees additional",
    },
  },
  AR: {
    "Class I": {
      description: "Low risk (Clase I under Disposición 2318/2002)",
      pathway: "Registro de Producto Médico via ANMAT",
      qsr: "Disposición 2318/2002 + Disposición 3266/2013 (GMP)",
      timeline: "3-6 months",
      establishment: "Argentine legal representative (Director Técnico) required",
      fees: "Registration fees ARS variable (subject to inflation adjustments)",
    },
    "Class II": {
      description: "Moderate risk (Clase II)",
      pathway: "Registro de Producto Médico via ANMAT with full technical review",
      qsr: "Disposición 2318/2002 + Full GMP compliance + Technical file + Risk management",
      timeline: "6-18 months",
      establishment: "Director Técnico required; GMP certificate; Certificate of Free Sale",
      fees: "Registration + technical review fees; GMP inspection costs",
    },
  },
};

const ISO_13485_CLAUSES = [
  {
    id: "4",
    title: "Quality Management System",
    subclauses: [
      { id: "4.1", title: "General Requirements", summary: "Establish, document, implement, and maintain a QMS. Define processes, their sequence, interaction, criteria for effectiveness, resources, monitoring, and improvement. Outsourced processes must be controlled.", critical: true },
      { id: "4.1.1", title: "General Requirements — Product Realization", summary: "Document roles for provision, control of outsourced work, and risk management for each medical device." },
      { id: "4.2", title: "Documentation Requirements", summary: "QMS documentation must include quality policy, quality objectives, quality manual, documented procedures, documents, and records required by this standard." },
      { id: "4.2.1", title: "General Documentation", summary: "Documentation must address regulatory requirements and the organization's QMS needs." },
      { id: "4.2.2", title: "Quality Manual", summary: "Establish and maintain a quality manual including scope, justified exclusions, documented procedures or references, and description of process interactions." },
      { id: "4.2.3", title: "Control of Documents", summary: "Documented procedure to control documents: approval, review, updates, identification of changes, availability, legibility, identification of external documents, and prevention of obsolete document use.", critical: true },
      { id: "4.2.4", title: "Control of Records", summary: "Records must remain legible, readily identifiable, and retrievable. Documented procedure for identification, storage, security, integrity, retrieval, retention time, and disposition.", critical: true },
      { id: "4.2.5", title: "Medical Device File", summary: "For each medical device type or family, establish and maintain one or more files containing or referencing documents generated to demonstrate conformity and QMS effectiveness." },
    ],
  },
  {
    id: "5",
    title: "Management Responsibility",
    subclauses: [
      { id: "5.1", title: "Management Commitment", summary: "Top management must demonstrate commitment by communicating regulatory and customer importance, establishing quality policy and objectives, conducting management reviews, and ensuring resource availability." },
      { id: "5.2", title: "Customer Focus", summary: "Ensure customer and applicable regulatory requirements are determined and met." },
      { id: "5.3", title: "Quality Policy", summary: "Quality policy must be appropriate to purpose, include commitment to comply with requirements and maintain QMS effectiveness, and be communicated and understood." },
      { id: "5.4", title: "Planning", summary: "Quality objectives must be established at relevant functions and levels. QMS planning must meet general requirements and quality objectives." },
      { id: "5.5", title: "Responsibility, Authority and Communication", summary: "Define and communicate responsibilities and authorities. Appoint management representative. Establish internal communication processes." },
      { id: "5.6", title: "Management Review", summary: "Review QMS at planned intervals for suitability, adequacy, and effectiveness. Include evaluation of improvement opportunities and need for changes. Maintain records of reviews.", critical: true },
    ],
  },
  {
    id: "6",
    title: "Resource Management",
    subclauses: [
      { id: "6.1", title: "Provision of Resources", summary: "Determine and provide resources needed to implement and maintain QMS, meet regulatory and customer requirements." },
      { id: "6.2", title: "Human Resources", summary: "Personnel performing QMS-affecting work must be competent based on education, training, skills, and experience. Determine competence, provide training, evaluate effectiveness, maintain records." },
      { id: "6.3", title: "Infrastructure", summary: "Determine, provide, and maintain infrastructure needed for conformity: buildings, workspace, process equipment (hardware and software), supporting services. Document maintenance requirements including intervals." },
      { id: "6.4", title: "Work Environment and Contamination Control", summary: "Determine and manage work environment needed for conformity. Document requirements for health, cleanliness, clothing if they could affect product quality. Establish contamination control arrangements as appropriate." },
    ],
  },
  {
    id: "7",
    title: "Product Realization",
    subclauses: [
      { id: "7.1", title: "Planning of Product Realization", summary: "Plan and develop processes needed for product realization consistent with QMS requirements. Determine quality objectives, need for processes and documentation, verification/validation/monitoring/testing, and records.", critical: true },
      { id: "7.2", title: "Customer-Related Processes", summary: "Determine product requirements including regulatory, delivery, and implied requirements. Review ability to meet requirements before commitment. Establish customer communication arrangements." },
      { id: "7.3", title: "Design and Development", summary: "Establish documented procedures for design and development. Plan and control design stages including review, verification, and validation activities. Manage design inputs, outputs, reviews, verification, validation, transfer, changes, and design history files.", critical: true },
      { id: "7.3.2", title: "Design and Development Planning", summary: "Document design plans including stages, reviews/verifications/validations, responsibilities, methods for traceability of design outputs to inputs, and resources needed." },
      { id: "7.3.3", title: "Design and Development Inputs", summary: "Determine and record inputs relating to functionality, performance, safety, regulatory requirements, risk management outputs, and applicable standards." },
      { id: "7.3.4", title: "Design and Development Outputs", summary: "Outputs must be verifiable against inputs and approved before release. Must include acceptance criteria, essential characteristics for safe and proper use, and reference purchasing/production/servicing information." },
      { id: "7.3.5", title: "Design and Development Review", summary: "Systematic reviews at suitable stages to evaluate ability to fulfill requirements and identify problems. Include representatives of functions concerned. Maintain records." },
      { id: "7.3.6", title: "Design and Development Verification", summary: "Verification performed per planned arrangements to ensure outputs meet input requirements. Maintain records of verification results and actions." },
      { id: "7.3.7", title: "Design and Development Validation", summary: "Validation under defined operating conditions per planned arrangements, including clinical evaluation or performance evaluation as applicable. Maintain records.", critical: true },
      { id: "7.3.8", title: "Design and Development Transfer", summary: "Document procedures for transfer of design outputs to manufacturing. Verify that outputs are suitable for manufacturing before becoming final production specifications." },
      { id: "7.3.9", title: "Control of Design and Development Changes", summary: "Identify, document, review, verify, validate as appropriate, and approve design changes before implementation. Maintain records." },
      { id: "7.3.10", title: "Design and Development Files", summary: "Maintain a design and development file for each medical device type or family." },
      { id: "7.4", title: "Purchasing", summary: "Ensure purchased product conforms to requirements. Evaluate and select suppliers based on ability to supply. Establish criteria for evaluation, selection, monitoring, and re-evaluation. Maintain records.", critical: true },
      { id: "7.5", title: "Production and Service Provision", summary: "Plan and carry out production and service provision under controlled conditions. Validate processes where output cannot be verified by subsequent monitoring. Establish requirements for cleanliness and contamination control. Implement servicing activities and verify they meet requirements.", critical: true },
      { id: "7.5.1", title: "Control of Production and Service Provision", summary: "Controlled conditions include: documented procedures, infrastructure, process parameters and monitoring, measuring equipment, and defined operations for labeling, packaging, and release." },
      { id: "7.5.2", title: "Cleanliness of Product", summary: "Document cleanliness requirements if product is cleaned before sterilization or its use, supplied non-sterile for sterilization, supplied as non-sterile but cleanliness is important, or agents are to be removed during manufacturing." },
      { id: "7.5.4", title: "Servicing Activities", summary: "When servicing is a specified requirement, document servicing procedures, reference materials, and measuring requirements. Analyze servicing records for potential use as complaint handling data." },
      { id: "7.5.6", title: "Validation of Processes for Production and Service Provision", summary: "Validate any process where the resulting output cannot be or is not verified by subsequent monitoring or measurement. This includes sterilization processes and aseptic processing.", critical: true },
      { id: "7.5.7", title: "Particular Requirements for Validation of Processes for Sterilization and Sterile Barrier Systems", summary: "Validate sterilization processes and sterile barrier system processes before implementation and after changes. Maintain records.", critical: true },
      { id: "7.5.8", title: "Identification", summary: "Identify product by suitable means throughout product realization. Identify product status with respect to monitoring and measurement requirements." },
      { id: "7.5.9", title: "Traceability", summary: "Document procedures for traceability. For implantable devices, require records of all components, materials, and work environment conditions used. Require distribution records to allow investigation.", critical: true },
      { id: "7.6", title: "Control of Monitoring and Measuring Equipment", summary: "Determine monitoring and measurement needed. Establish documented procedures to ensure valid results. Calibrate or verify at specified intervals. Adjust as necessary. Identify calibration status. Safeguard from adjustments. Maintain calibration records.", critical: true },
    ],
  },
  {
    id: "8",
    title: "Measurement, Analysis and Improvement",
    subclauses: [
      { id: "8.1", title: "General", summary: "Plan and implement monitoring, measurement, analysis, and improvement processes needed to demonstrate conformity, ensure QMS conformity, and maintain QMS effectiveness." },
      { id: "8.2", title: "Monitoring and Measurement", summary: "Monitor information on whether customer requirements are met (feedback system). Implement complaint handling procedures. Report to regulatory authorities as required. Conduct internal audits at planned intervals. Monitor and measure QMS processes and product.", critical: true },
      { id: "8.2.1", title: "Feedback", summary: "Gather and monitor information on whether the organization has met customer requirements. This serves as one measurement of QMS effectiveness. Include feedback from production and post-production activities." },
      { id: "8.2.2", title: "Complaint Handling", summary: "Document procedures for timely complaint handling per applicable regulatory requirements. Investigate all complaints. Determine if complaint is a reportable event. If complaint is not investigated, document justification.", critical: true },
      { id: "8.2.3", title: "Reporting to Regulatory Authorities", summary: "If regulatory requirements require notification of complaints meeting reporting criteria for adverse events or issuance of advisory notices, document procedures for reporting.", critical: true },
      { id: "8.2.4", title: "Internal Audit", summary: "Conduct internal audits at planned intervals. Document audit program, criteria, scope, frequency, methods. Ensure auditor objectivity and impartiality. Document procedure for planning, conducting, recording, and reporting audits.", critical: true },
      { id: "8.2.5", title: "Monitoring and Measurement of Processes", summary: "Apply suitable methods for monitoring and measurement of QMS processes. When planned results are not achieved, take correction and corrective action as appropriate." },
      { id: "8.2.6", title: "Monitoring and Measurement of Product", summary: "Monitor and measure characteristics of product to verify product requirements are fulfilled. Maintain evidence of conformity with acceptance criteria. Record identity of person authorizing release.", critical: true },
      { id: "8.3", title: "Control of Nonconforming Product", summary: "Ensure nonconforming product is identified and controlled to prevent unintended use or delivery. Document procedure defining controls, responsibilities, and authorities. Take appropriate action to the effects of nonconformity. Maintain records.", critical: true },
      { id: "8.4", title: "Analysis of Data", summary: "Determine, collect, and analyze appropriate data to demonstrate QMS suitability, adequacy, and effectiveness. Include data from monitoring and measurement and other relevant sources (feedback, conformity, trends, suppliers, audits, service reports)." },
      { id: "8.5", title: "Improvement", summary: "Identify and implement changes necessary to ensure and maintain QMS suitability, adequacy, and effectiveness. Implement corrective actions to eliminate causes of nonconformities. Implement preventive actions to eliminate causes of potential nonconformities.", critical: true },
      { id: "8.5.1", title: "Corrective Action (CAPA)", summary: "Document procedure for: reviewing nonconformities (including complaints), determining causes, evaluating need for action, planning and implementing action, recording results, and reviewing effectiveness of corrective action taken.", critical: true },
      { id: "8.5.2", title: "Preventive Action", summary: "Document procedure for: determining potential nonconformities and their causes, evaluating need for action, planning and implementing action, recording results, and reviewing effectiveness of preventive action taken.", critical: true },
      { id: "8.5.3", title: "Advisory Notices and Recalls", summary: "Document procedures for issuing advisory notices and implementing recalls in accordance with applicable regulatory requirements. Ability to issue at any time. Maintain records of investigation and recall actions.", critical: true },
    ],
  },
];

const STANDARDS_MAP = {
  "ISO 13485:2016": {
    title: "Quality Management Systems — Requirements for Regulatory Purposes",
    category: "QMS",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["all"],
    summary: "Core QMS standard for medical devices. Required directly or recognized in all major markets. Covers design controls, production, CAPA, risk management integration, and regulatory compliance.",
  },
  "ISO 14971:2019": {
    title: "Application of Risk Management to Medical Devices",
    category: "Risk Management",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["all"],
    summary: "Defines the risk management process for medical devices throughout the lifecycle. Required or recognized universally. Covers hazard identification, risk estimation, risk evaluation, risk control, and residual risk evaluation.",
  },
  "IEC 62366-1:2015+A1:2020": {
    title: "Application of Usability Engineering to Medical Devices",
    category: "Usability",
    applicableMarkets: ["US", "EU", "UK", "BR"],
    deviceTypes: ["all"],
    summary: "Process for analyzing, specifying, developing, and evaluating usability of medical devices. Essential for user interface design, use-related risk analysis, formative and summative evaluations.",
  },
  "IEC 60601-1:2005+A1+A2": {
    title: "General Requirements for Basic Safety and Essential Performance of Medical Electrical Equipment",
    category: "Electrical Safety",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["electrical", "electronic", "software-driven"],
    summary: "Fundamental safety standard for medical electrical equipment. Covers electrical safety, mechanical safety, radiation, temperature, accuracy, and essential performance.",
  },
  "ISO 10993 Series": {
    title: "Biological Evaluation of Medical Devices",
    category: "Biocompatibility",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["patient-contact", "implantable", "body-fluid-contact"],
    summary: "Framework for biological evaluation of medical devices based on nature and duration of body contact. Part 1 defines evaluation/testing framework. Key parts: -3 (genotoxicity), -4 (blood interaction), -5 (cytotoxicity), -6 (implant effects), -10 (irritation/sensitization), -11 (systemic toxicity).",
  },
  "ISO 11135:2014": {
    title: "Sterilization of Healthcare Products — Ethylene Oxide",
    category: "Sterilization",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["sterile-EO"],
    summary: "Requirements for development, validation, and routine control of EO sterilization process for medical devices.",
  },
  "ISO 11137 Series": {
    title: "Sterilization of Healthcare Products — Radiation",
    category: "Sterilization",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["sterile-radiation"],
    summary: "Requirements for development, validation, and routine control of radiation sterilization (gamma, e-beam, X-ray).",
  },
  "ISO 11607-1/-2": {
    title: "Packaging for Terminally Sterilized Medical Devices",
    category: "Packaging",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["sterile"],
    summary: "Requirements for materials, sterile barrier systems, and packaging systems for terminally sterilized medical devices. Part 1: requirements for materials. Part 2: validation of forming, sealing, and assembly processes.",
  },
  "IEC 62304:2006+A1:2015": {
    title: "Medical Device Software — Software Life Cycle Processes",
    category: "Software",
    applicableMarkets: ["US", "EU", "UK", "BR"],
    deviceTypes: ["software", "software-driven"],
    summary: "Framework for lifecycle processes for medical device software development and maintenance. Defines software safety classification and corresponding requirements for planning, analysis, design, implementation, testing, and maintenance.",
  },
  "ISO 15223-1:2021": {
    title: "Symbols to be Used with Information Supplied by the Manufacturer",
    category: "Labeling",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["all"],
    summary: "Standardized symbols for use on medical device labels, labeling, and information supplied by the manufacturer.",
  },
  "EN 556-1:2001": {
    title: "Requirements for Terminally Sterilized Devices to be Labeled 'STERILE'",
    category: "Sterilization",
    applicableMarkets: ["EU", "UK"],
    deviceTypes: ["sterile"],
    summary: "Specifies requirements to be met in order for a terminally sterilized medical device to bear the label 'STERILE' and SAL of 10⁻⁶.",
  },
  "ISO 20417:2021": {
    title: "Information to be Supplied by the Manufacturer",
    category: "Labeling",
    applicableMarkets: ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
    deviceTypes: ["all"],
    summary: "General requirements for information to be supplied with medical devices: labels, instructions for use, technical descriptions.",
  },
};

const TESTING_REQUIREMENTS = {
  "patient-contact": {
    biocompatibility: {
      title: "Biocompatibility Testing (ISO 10993)",
      tests: [
        { name: "Cytotoxicity (ISO 10993-5)", required: "all", duration: "2-4 weeks" },
        { name: "Sensitization (ISO 10993-10)", required: "all", duration: "4-8 weeks" },
        { name: "Irritation (ISO 10993-10/23)", required: "all", duration: "2-6 weeks" },
        { name: "Systemic Toxicity (ISO 10993-11)", required: "prolonged+permanent", duration: "4-12 weeks" },
        { name: "Genotoxicity (ISO 10993-3)", required: "prolonged+permanent", duration: "6-12 weeks" },
        { name: "Implantation (ISO 10993-6)", required: "implantable", duration: "12-26 weeks" },
        { name: "Hemocompatibility (ISO 10993-4)", required: "blood-contact", duration: "4-8 weeks" },
      ],
    },
  },
  electrical: {
    safety: {
      title: "Electrical Safety Testing (IEC 60601-1)",
      tests: [
        { name: "Electrical Safety — General (60601-1)", required: "all-electrical", duration: "4-8 weeks" },
        { name: "EMC Testing (IEC 60601-1-2)", required: "all-electrical", duration: "4-8 weeks" },
        { name: "Software Safety Classification (IEC 62304)", required: "software-driven", duration: "N/A — process" },
        { name: "Usability Engineering (IEC 62366-1)", required: "all", duration: "8-16 weeks" },
        { name: "Alarm Systems (IEC 60601-1-8)", required: "alarm-equipped", duration: "2-4 weeks" },
      ],
    },
  },
  sterile: {
    sterilization: {
      title: "Sterilization Validation",
      tests: [
        { name: "Bioburden Testing (ISO 11737-1)", required: "all-sterile", duration: "2-4 weeks" },
        { name: "Sterility Testing (ISO 11737-2)", required: "all-sterile", duration: "2-4 weeks" },
        { name: "EO Sterilization Validation (ISO 11135)", required: "EO-sterilized", duration: "8-16 weeks" },
        { name: "Radiation Sterilization Validation (ISO 11137)", required: "radiation-sterilized", duration: "8-12 weeks" },
        { name: "Packaging Validation (ISO 11607)", required: "all-sterile", duration: "4-12 weeks" },
        { name: "Accelerated Aging / Shelf Life (ASTM F1980)", required: "all-sterile", duration: "8-16 weeks" },
        { name: "Package Integrity — Seal Strength (ASTM F88)", required: "all-sterile", duration: "1-2 weeks" },
        { name: "Package Integrity — Dye Penetration / Bubble (ASTM F1929/F2095)", required: "all-sterile", duration: "1-2 weeks" },
      ],
    },
  },
  general: {
    design: {
      title: "General Design & Performance",
      tests: [
        { name: "Risk Management File (ISO 14971)", required: "all", duration: "Ongoing — lifecycle" },
        { name: "Essential Performance Testing", required: "all", duration: "4-12 weeks" },
        { name: "Labeling Review (ISO 15223-1 / 21 CFR 801)", required: "all", duration: "2-4 weeks" },
        { name: "Shelf Life / Stability Testing", required: "all", duration: "Real-time or accelerated" },
        { name: "Transportation / Distribution Simulation (ISTA/ASTM D4169)", required: "shipped-products", duration: "2-4 weeks" },
        { name: "Clinical Evaluation / Literature Review", required: "all", duration: "4-16 weeks" },
      ],
    },
  },
};

const GAP_ANALYSIS_ITEMS = [
  { id: "qms-1", category: "QMS Foundation", item: "Quality Manual documented and current", clause: "4.2.2", critical: true },
  { id: "qms-2", category: "QMS Foundation", item: "Quality Policy established, communicated, understood", clause: "5.3", critical: true },
  { id: "qms-3", category: "QMS Foundation", item: "Quality Objectives defined at relevant functions/levels", clause: "5.4.1", critical: false },
  { id: "qms-4", category: "QMS Foundation", item: "Document control procedure implemented", clause: "4.2.3", critical: true },
  { id: "qms-5", category: "QMS Foundation", item: "Record control procedure implemented", clause: "4.2.4", critical: true },
  { id: "qms-6", category: "QMS Foundation", item: "Medical Device File(s) established per device family", clause: "4.2.5", critical: true },
  { id: "mgmt-1", category: "Management", item: "Management Representative appointed", clause: "5.5.2", critical: true },
  { id: "mgmt-2", category: "Management", item: "Management Reviews conducted at planned intervals with required inputs/outputs", clause: "5.6", critical: true },
  { id: "mgmt-3", category: "Management", item: "Internal communication processes established", clause: "5.5.3", critical: false },
  { id: "res-1", category: "Resources", item: "Competence requirements defined for QMS-affecting personnel", clause: "6.2", critical: true },
  { id: "res-2", category: "Resources", item: "Training effectiveness evaluated and records maintained", clause: "6.2", critical: true },
  { id: "res-3", category: "Resources", item: "Infrastructure documented with maintenance requirements/intervals", clause: "6.3", critical: false },
  { id: "res-4", category: "Resources", item: "Work environment requirements documented (cleanliness, contamination control)", clause: "6.4", critical: false },
  { id: "dc-1", category: "Design Controls", item: "Design and Development procedure documented", clause: "7.3.1", critical: true },
  { id: "dc-2", category: "Design Controls", item: "Design Plan with stages, reviews, V&V activities, responsibilities", clause: "7.3.2", critical: true },
  { id: "dc-3", category: "Design Controls", item: "Design Inputs documented (functional, performance, safety, regulatory, risk)", clause: "7.3.3", critical: true },
  { id: "dc-4", category: "Design Controls", item: "Design Outputs meet input requirements and include acceptance criteria", clause: "7.3.4", critical: true },
  { id: "dc-5", category: "Design Controls", item: "Design Reviews conducted at suitable stages with records", clause: "7.3.5", critical: true },
  { id: "dc-6", category: "Design Controls", item: "Design Verification performed and recorded", clause: "7.3.6", critical: true },
  { id: "dc-7", category: "Design Controls", item: "Design Validation performed under defined operating conditions", clause: "7.3.7", critical: true },
  { id: "dc-8", category: "Design Controls", item: "Design Transfer procedure documented and executed", clause: "7.3.8", critical: true },
  { id: "dc-9", category: "Design Controls", item: "Design Change control procedure implemented", clause: "7.3.9", critical: true },
  { id: "dc-10", category: "Design Controls", item: "Design History File (DHF) maintained per device", clause: "7.3.10", critical: true },
  { id: "pur-1", category: "Purchasing", item: "Supplier evaluation and selection criteria documented", clause: "7.4.1", critical: true },
  { id: "pur-2", category: "Purchasing", item: "Approved Supplier List maintained with monitoring/re-evaluation", clause: "7.4.1", critical: true },
  { id: "pur-3", category: "Purchasing", item: "Purchasing data specifies requirements adequately", clause: "7.4.2", critical: false },
  { id: "pur-4", category: "Purchasing", item: "Incoming inspection/verification procedures established", clause: "7.4.3", critical: true },
  { id: "prod-1", category: "Production", item: "Production procedures/work instructions documented", clause: "7.5.1", critical: true },
  { id: "prod-2", category: "Production", item: "Process validation performed for special processes", clause: "7.5.6", critical: true },
  { id: "prod-3", category: "Production", item: "Sterilization process validation (if applicable)", clause: "7.5.7", critical: true },
  { id: "prod-4", category: "Production", item: "Product identification throughout realization", clause: "7.5.8", critical: true },
  { id: "prod-5", category: "Production", item: "Traceability system implemented (especially for implantables)", clause: "7.5.9", critical: true },
  { id: "prod-6", category: "Production", item: "Calibration program for monitoring/measuring equipment", clause: "7.6", critical: true },
  { id: "prod-7", category: "Production", item: "Cleanliness requirements documented (if applicable)", clause: "7.5.2", critical: false },
  { id: "fb-1", category: "Feedback & Improvement", item: "Customer feedback / post-market surveillance system", clause: "8.2.1", critical: true },
  { id: "fb-2", category: "Feedback & Improvement", item: "Complaint handling procedure documented and implemented", clause: "8.2.2", critical: true },
  { id: "fb-3", category: "Feedback & Improvement", item: "Regulatory reporting procedures (MDR, MedWatch, vigilance)", clause: "8.2.3", critical: true },
  { id: "fb-4", category: "Feedback & Improvement", item: "Internal audit program planned and executed", clause: "8.2.4", critical: true },
  { id: "fb-5", category: "Feedback & Improvement", item: "Nonconforming product control procedure", clause: "8.3", critical: true },
  { id: "fb-6", category: "Feedback & Improvement", item: "CAPA (Corrective Action) procedure implemented", clause: "8.5.1", critical: true },
  { id: "fb-7", category: "Feedback & Improvement", item: "CAPA (Preventive Action) procedure implemented", clause: "8.5.2", critical: true },
  { id: "fb-8", category: "Feedback & Improvement", item: "Advisory notice / recall procedure documented", clause: "8.5.3", critical: true },
  { id: "fb-9", category: "Feedback & Improvement", item: "Data analysis performed on QMS data (trends, suppliers, processes)", clause: "8.4", critical: false },
];

// ═══════════════════════════════════════════════════════════════
// MAIN APPLICATION COMPONENT
// ═══════════════════════════════════════════════════════════════

const TABS = [
  { id: "dashboard", label: "Dashboard", icon: "◈" },
  { id: "profile", label: "Product Profile", icon: "⬡" },
  { id: "matrix", label: "Requirements Matrix", icon: "▦" },
  { id: "gap", label: "Gap Analysis", icon: "◉" },
  { id: "standards", label: "Standards Library", icon: "◆" },
  { id: "chat", label: "AI Advisor", icon: "◎" },
];

export default function RegulatoryIntelligenceTool() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [productProfile, setProductProfile] = useState({
    name: "",
    description: "",
    classUS: "",
    classEU: "",
    deviceType: [],
    contactType: "",
    contactDuration: "",
    sterile: false,
    sterilizationMethod: "",
    hasSoftware: false,
    softwareSafetyClass: "",
    isElectrical: false,
    isImplantable: false,
    targetMarkets: [],
    intendedUse: "",
    predicateDevice: "",
  });
  const [gapStatuses, setGapStatuses] = useState({});
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [selectedStandard, setSelectedStandard] = useState(null);
  const [selectedClause, setSelectedClause] = useState(null);
  const [expandedSections, setExpandedSections] = useState({});

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const toggleSection = (id) => {
    setExpandedSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // ── Product Profile Helpers ──
  const updateProfile = (field, value) => {
    setProductProfile((prev) => ({ ...prev, [field]: value }));
  };

  const toggleArrayField = (field, value) => {
    setProductProfile((prev) => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter((v) => v !== value)
        : [...prev[field], value],
    }));
  };

  // ── Gap Analysis Helpers ──
  const setGapStatus = (id, status) => {
    setGapStatuses((prev) => ({ ...prev, [id]: status }));
  };

  const getGapStats = () => {
    const total = GAP_ANALYSIS_ITEMS.length;
    const compliant = Object.values(gapStatuses).filter((s) => s === "compliant").length;
    const partial = Object.values(gapStatuses).filter((s) => s === "partial").length;
    const nonCompliant = Object.values(gapStatuses).filter((s) => s === "non-compliant").length;
    const notAssessed = total - compliant - partial - nonCompliant;
    return { total, compliant, partial, nonCompliant, notAssessed };
  };

  // ── Chat Helpers ──
  const buildSystemPrompt = () => {
    const profileStr = productProfile.name
      ? `\n\nCurrent Product Profile:\n- Name: ${productProfile.name}\n- Description: ${productProfile.description}\n- US Classification: ${productProfile.classUS}\n- EU Classification: ${productProfile.classEU}\n- Target Markets: ${productProfile.targetMarkets.join(", ")}\n- Patient Contact: ${productProfile.contactType} (${productProfile.contactDuration})\n- Sterile: ${productProfile.sterile ? "Yes (" + productProfile.sterilizationMethod + ")" : "No"}\n- Software: ${productProfile.hasSoftware ? "Yes (Class " + productProfile.softwareSafetyClass + ")" : "No"}\n- Electrical: ${productProfile.isElectrical ? "Yes" : "No"}\n- Implantable: ${productProfile.isImplantable ? "Yes" : "No"}\n- Intended Use: ${productProfile.intendedUse}\n- Predicate Device: ${productProfile.predicateDevice}`
      : "";

    const gapStats = getGapStats();
    const gapStr =
      gapStats.compliant + gapStats.partial + gapStats.nonCompliant > 0
        ? `\n\nGap Analysis Status: ${gapStats.compliant} compliant, ${gapStats.partial} partial, ${gapStats.nonCompliant} non-compliant, ${gapStats.notAssessed} not assessed out of ${gapStats.total} items.`
        : "";

    return `You are a world-class medical device regulatory expert assistant. You have deep expertise in:
- ISO 13485:2016 (Quality Management Systems)
- FDA 21 CFR 820 (Quality System Regulation) and 510(k)/De Novo pathways
- EU MDR 2017/745 (European Medical Device Regulation)
- UK MDR 2002 (as amended) and UKCA marking
- ANVISA (Brazil) - RDC 751/2022, RDC 665/2022
- COFEPRIS (Mexico) - NOM-241-SSA1-2021
- INVIMA (Colombia) - Decreto 4725 de 2005
- ANMAT (Argentina) - Disposición 2318/2002
- ISO 14971 (Risk Management), IEC 60601-1 (Electrical Safety), ISO 10993 (Biocompatibility), IEC 62304 (Software), IEC 62366 (Usability), ISO 11607 (Packaging), ISO 11135/11137 (Sterilization)

You provide precise, actionable regulatory guidance. When discussing requirements, always specify the applicable regulation, clause, or standard. Compare market-specific requirements when relevant. Be direct and practical — the user is a quality management professional at a medical device company working with Class I and Class II devices.
${profileStr}${gapStr}

When the user asks about requirements for a specific market or product type, structure your response by market, listing the specific regulatory requirements, applicable standards, testing needed, and submission pathway. Always mention timelines and costs where possible.`;
  };

  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;

    const userMsg = { role: "user", content: chatInput.trim() };
    const newMessages = [...chatMessages, userMsg];
    setChatMessages(newMessages);
    setChatInput("");
    setChatLoading(true);

    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: buildSystemPrompt(),
          messages: newMessages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      const data = await response.json();
      const assistantContent = data.content
        ?.map((block) => block.text || "")
        .filter(Boolean)
        .join("\n");

      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: assistantContent || "I apologize, I was unable to generate a response. Please try again." },
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Connection error. Please try again. The AI advisor requires an active connection." },
      ]);
    }
    setChatLoading(false);
  };

  // ── Computed Data ──
  const applicableStandards = Object.entries(STANDARDS_MAP).filter(([key, std]) => {
    if (productProfile.targetMarkets.length === 0) return true;
    return productProfile.targetMarkets.some((m) => std.applicableMarkets.includes(m));
  });

  const getApplicableTests = () => {
    const tests = [];
    tests.push(...(TESTING_REQUIREMENTS.general?.design?.tests || []));
    if (productProfile.contactType && productProfile.contactType !== "none") {
      tests.push(...(TESTING_REQUIREMENTS["patient-contact"]?.biocompatibility?.tests || []));
    }
    if (productProfile.isElectrical || productProfile.hasSoftware) {
      tests.push(...(TESTING_REQUIREMENTS.electrical?.safety?.tests || []));
    }
    if (productProfile.sterile) {
      tests.push(...(TESTING_REQUIREMENTS.sterile?.sterilization?.tests || []));
    }
    return tests;
  };

  // ═══════════════════════════════════════════════════════════════
  // RENDER FUNCTIONS
  // ═══════════════════════════════════════════════════════════════

  const renderDashboard = () => {
    const gapStats = getGapStats();
    const profileComplete = productProfile.name && productProfile.targetMarkets.length > 0;
    const marketsSelected = productProfile.targetMarkets.length;

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {/* Welcome Header */}
        <div style={{ background: "linear-gradient(135deg, #0a1628 0%, #1a2d50 50%, #0f2040 100%)", borderRadius: 16, padding: "32px 36px", color: "#fff", position: "relative", overflow: "hidden" }}>
          <div style={{ position: "absolute", top: 0, right: 0, width: 300, height: 300, background: "radial-gradient(circle, rgba(56,189,248,0.08) 0%, transparent 70%)", pointerEvents: "none" }} />
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, letterSpacing: "-0.02em", fontFamily: "'Source Serif 4', Georgia, serif" }}>Regulatory Intelligence Center</h2>
          <p style={{ color: "#94a3b8", marginTop: 8, fontSize: 14, lineHeight: 1.6, maxWidth: 600 }}>
            Your unified compliance hub for ISO 13485 and multi-market medical device regulatory requirements across the US, EU, UK, and Latin America.
          </p>
        </div>

        {/* Quick Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
          <StatCard label="Product Profile" value={profileComplete ? "✓ Configured" : "Not Set"} sublabel={profileComplete ? productProfile.name : "Configure in Product Profile tab"} accent={profileComplete ? "#10b981" : "#f59e0b"} />
          <StatCard label="Target Markets" value={marketsSelected} sublabel={marketsSelected > 0 ? productProfile.targetMarkets.map((m) => MARKETS[m]?.flag).join(" ") : "Select markets in Product Profile"} accent="#3b82f6" />
          <StatCard label="Applicable Standards" value={applicableStandards.length} sublabel="Standards mapped to your profile" accent="#8b5cf6" />
          <StatCard label="Gap Analysis" value={`${gapStats.compliant}/${gapStats.total}`} sublabel={`${gapStats.nonCompliant} gaps · ${gapStats.partial} partial · ${gapStats.notAssessed} unassessed`} accent={gapStats.nonCompliant > 0 ? "#ef4444" : "#10b981"} />
        </div>

        {/* Quick Actions */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
          <ActionCard title="Configure Product Profile" description="Define your device characteristics, classification, and target markets to generate market-specific requirements." action={() => setActiveTab("profile")} buttonLabel="Set Up Profile →" />
          <ActionCard title="View Requirements Matrix" description="See testing, documentation, and submission requirements broken down by each target market." action={() => setActiveTab("matrix")} buttonLabel="View Matrix →" />
          <ActionCard title="Run Gap Analysis" description="Assess your QMS against ISO 13485 clause-by-clause and identify compliance gaps." action={() => setActiveTab("gap")} buttonLabel="Start Analysis →" />
          <ActionCard title="Ask the AI Advisor" description="Get instant answers on regulatory questions, testing requirements, submission pathways, and more." action={() => setActiveTab("chat")} buttonLabel="Open Chat →" />
        </div>

        {/* Market Overview */}
        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: 16, fontWeight: 600, color: "#0f172a", fontFamily: "'Source Serif 4', Georgia, serif" }}>Market Overview</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
            {Object.entries(MARKETS).map(([code, market]) => (
              <div key={code} style={{ padding: "14px 16px", borderRadius: 10, border: `1px solid ${productProfile.targetMarkets.includes(code) ? market.color + "40" : "#e2e8f0"}`, background: productProfile.targetMarkets.includes(code) ? market.color + "08" : "#fafafa", transition: "all 0.2s" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 20 }}>{market.flag}</span>
                  <span style={{ fontWeight: 600, fontSize: 13, color: "#0f172a" }}>{market.name}</span>
                </div>
                <div style={{ fontSize: 12, color: "#64748b" }}>{market.agency}</div>
                {productProfile.targetMarkets.includes(code) && (
                  <div style={{ marginTop: 6, fontSize: 11, color: market.color, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>● Active Market</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderProductProfile = () => (
    <div style={{ display: "flex", flexDirection: "column", gap: 24, maxWidth: 900 }}>
      <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 28 }}>
        <h3 style={{ margin: "0 0 20px 0", fontSize: 18, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>Device Information</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <FormField label="Device Name" value={productProfile.name} onChange={(v) => updateProfile("name", v)} placeholder="e.g., WoundSeal Pro Bandage System" fullWidth />
          <FormField label="Predicate Device (510(k))" value={productProfile.predicateDevice} onChange={(v) => updateProfile("predicateDevice", v)} placeholder="e.g., K123456" />
        </div>
        <div style={{ marginTop: 16 }}>
          <FormField label="Device Description" value={productProfile.description} onChange={(v) => updateProfile("description", v)} placeholder="Brief description of the device, its components, and function..." textarea />
        </div>
        <div style={{ marginTop: 16 }}>
          <FormField label="Intended Use / Indications for Use" value={productProfile.intendedUse} onChange={(v) => updateProfile("intendedUse", v)} placeholder="The device is intended for..." textarea />
        </div>
      </div>

      <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 28 }}>
        <h3 style={{ margin: "0 0 20px 0", fontSize: 18, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>Classification</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <SelectField label="US FDA Classification" value={productProfile.classUS} onChange={(v) => updateProfile("classUS", v)} options={[{ v: "", l: "Select..." }, { v: "Class I", l: "Class I — Low Risk" }, { v: "Class I (510(k) required)", l: "Class I — 510(k) Required" }, { v: "Class II", l: "Class II — Moderate Risk (510(k))" }, { v: "Class II (De Novo)", l: "Class II — De Novo" }]} />
          <SelectField label="EU MDR Classification" value={productProfile.classEU} onChange={(v) => updateProfile("classEU", v)} options={[{ v: "", l: "Select..." }, { v: "Class I", l: "Class I" }, { v: "Class I (sterile)", l: "Class I — Sterile" }, { v: "Class I (measuring)", l: "Class I — Measuring Function" }, { v: "Class I (reusable surgical)", l: "Class I — Reusable Surgical" }, { v: "Class IIa", l: "Class IIa" }, { v: "Class IIb", l: "Class IIb" }]} />
        </div>
      </div>

      <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 28 }}>
        <h3 style={{ margin: "0 0 20px 0", fontSize: 18, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>Device Characteristics</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <SelectField label="Patient Contact Type" value={productProfile.contactType} onChange={(v) => updateProfile("contactType", v)} options={[{ v: "", l: "Select..." }, { v: "none", l: "No patient contact" }, { v: "intact-skin", l: "Intact skin surface" }, { v: "mucosal-membrane", l: "Mucosal membrane" }, { v: "breached-skin", l: "Breached/compromised skin" }, { v: "blood-path-indirect", l: "Blood path — indirect" }, { v: "blood-contact", l: "Blood contacting" }, { v: "tissue-bone", l: "Tissue/bone contact" }, { v: "implant", l: "Implant" }]} />
          <SelectField label="Contact Duration" value={productProfile.contactDuration} onChange={(v) => updateProfile("contactDuration", v)} options={[{ v: "", l: "Select..." }, { v: "limited", l: "Limited (< 24 hours)" }, { v: "prolonged", l: "Prolonged (24 hrs – 30 days)" }, { v: "permanent", l: "Permanent (> 30 days)" }]} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginTop: 16 }}>
          <ToggleField label="Sterile Device" checked={productProfile.sterile} onChange={(v) => updateProfile("sterile", v)} />
          <ToggleField label="Contains Software" checked={productProfile.hasSoftware} onChange={(v) => updateProfile("hasSoftware", v)} />
          <ToggleField label="Electrical / Electronic" checked={productProfile.isElectrical} onChange={(v) => updateProfile("isElectrical", v)} />
        </div>
        {productProfile.sterile && (
          <div style={{ marginTop: 16 }}>
            <SelectField label="Sterilization Method" value={productProfile.sterilizationMethod} onChange={(v) => updateProfile("sterilizationMethod", v)} options={[{ v: "", l: "Select..." }, { v: "EO", l: "Ethylene Oxide (EO)" }, { v: "gamma", l: "Gamma Radiation" }, { v: "e-beam", l: "Electron Beam" }, { v: "steam", l: "Steam (Autoclave)" }, { v: "dry-heat", l: "Dry Heat" }, { v: "other", l: "Other" }]} />
          </div>
        )}
        {productProfile.hasSoftware && (
          <div style={{ marginTop: 16 }}>
            <SelectField label="Software Safety Classification (IEC 62304)" value={productProfile.softwareSafetyClass} onChange={(v) => updateProfile("softwareSafetyClass", v)} options={[{ v: "", l: "Select..." }, { v: "A", l: "Class A — No injury or damage to health" }, { v: "B", l: "Class B — Non-serious injury" }, { v: "C", l: "Class C — Death or serious injury possible" }]} />
          </div>
        )}
      </div>

      <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 28 }}>
        <h3 style={{ margin: "0 0 20px 0", fontSize: 18, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>Target Markets</h3>
        <p style={{ fontSize: 13, color: "#64748b", margin: "0 0 16px 0" }}>Select all markets where you intend to sell this device:</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10 }}>
          {Object.entries(MARKETS).map(([code, market]) => (
            <button key={code} onClick={() => toggleArrayField("targetMarkets", code)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", borderRadius: 10, border: `2px solid ${productProfile.targetMarkets.includes(code) ? market.color : "#e2e8f0"}`, background: productProfile.targetMarkets.includes(code) ? market.color + "0d" : "#fff", cursor: "pointer", transition: "all 0.2s" }}>
              <span style={{ fontSize: 22 }}>{market.flag}</span>
              <div style={{ textAlign: "left" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#0f172a" }}>{market.name}</div>
                <div style={{ fontSize: 11, color: "#64748b" }}>{market.agency}</div>
              </div>
              {productProfile.targetMarkets.includes(code) && <span style={{ marginLeft: "auto", color: market.color, fontWeight: 700, fontSize: 18 }}>✓</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const renderRequirementsMatrix = () => {
    const markets = productProfile.targetMarkets.length > 0 ? productProfile.targetMarkets : Object.keys(MARKETS);
    const tests = getApplicableTests();

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {!productProfile.name && (
          <div style={{ background: "#fffbeb", border: "1px solid #fbbf24", borderRadius: 10, padding: "14px 18px", fontSize: 13, color: "#92400e" }}>
            ⚠️ Configure your Product Profile first for tailored requirements. Showing general requirements for all markets.
          </div>
        )}

        {/* Submission Pathways by Market */}
        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>Submission Pathways by Market</h3>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  <th style={thStyle}>Market</th>
                  <th style={thStyle}>Class</th>
                  <th style={thStyle}>Pathway</th>
                  <th style={thStyle}>QMS Requirement</th>
                  <th style={thStyle}>Timeline</th>
                  <th style={thStyle}>Establishment</th>
                </tr>
              </thead>
              <tbody>
                {markets.map((mkt) => {
                  const classKey =
                    mkt === "EU"
                      ? productProfile.classEU || "Class IIa"
                      : productProfile.classUS?.includes("Class II")
                      ? "Class II"
                      : productProfile.classUS?.includes("Class I")
                      ? "Class I"
                      : "Class II";
                  const info = DEVICE_CLASSIFICATIONS[mkt]?.[classKey] || DEVICE_CLASSIFICATIONS[mkt]?.["Class II"] || DEVICE_CLASSIFICATIONS[mkt]?.["Class I"];
                  if (!info) return null;
                  return (
                    <tr key={mkt} style={{ borderBottom: "1px solid #e2e8f0" }}>
                      <td style={tdStyle}>
                        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <span>{MARKETS[mkt].flag}</span>
                          <span style={{ fontWeight: 600 }}>{MARKETS[mkt].agency}</span>
                        </span>
                      </td>
                      <td style={tdStyle}><span style={{ background: "#f1f5f9", padding: "2px 8px", borderRadius: 4, fontSize: 12, fontWeight: 600 }}>{classKey}</span></td>
                      <td style={{ ...tdStyle, maxWidth: 220 }}>{info.pathway}</td>
                      <td style={{ ...tdStyle, maxWidth: 220 }}>{info.qsr}</td>
                      <td style={tdStyle}><span style={{ whiteSpace: "nowrap" }}>{info.timeline}</span></td>
                      <td style={{ ...tdStyle, maxWidth: 200 }}>{info.establishment}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Testing Requirements */}
        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>Testing Requirements</h3>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  <th style={thStyle}>Test</th>
                  <th style={thStyle}>Applicability</th>
                  <th style={thStyle}>Est. Duration</th>
                  <th style={thStyle}>Status</th>
                </tr>
              </thead>
              <tbody>
                {tests.map((test, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ ...tdStyle, fontWeight: 500 }}>{test.name}</td>
                    <td style={tdStyle}><span style={{ fontSize: 11, color: "#64748b" }}>{test.required}</span></td>
                    <td style={tdStyle}>{test.duration}</td>
                    <td style={tdStyle}>
                      <span style={{ background: "#fef3c7", color: "#92400e", padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600 }}>Pending</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Applicable Standards */}
        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>Applicable Standards</h3>
          <div style={{ display: "grid", gap: 10 }}>
            {applicableStandards.map(([key, std]) => (
              <div key={key} style={{ padding: "12px 16px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fafafa" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <span style={{ fontWeight: 600, fontSize: 13, color: "#0f172a" }}>{key}</span>
                    <span style={{ fontSize: 12, color: "#64748b", marginLeft: 8 }}>{std.title}</span>
                  </div>
                  <span style={{ background: getCategoryColor(std.category), color: "#fff", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, textTransform: "uppercase", whiteSpace: "nowrap" }}>{std.category}</span>
                </div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 6 }}>{std.summary}</div>
                <div style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap" }}>
                  {std.applicableMarkets.map((m) => (
                    <span key={m} style={{ fontSize: 14 }} title={MARKETS[m]?.name}>{MARKETS[m]?.flag}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderGapAnalysis = () => {
    const stats = getGapStats();
    const categories = [...new Set(GAP_ANALYSIS_ITEMS.map((i) => i.category))];

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {/* Stats bar */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
          <MiniStat label="Total Items" value={stats.total} color="#475569" />
          <MiniStat label="Compliant" value={stats.compliant} color="#10b981" />
          <MiniStat label="Partial" value={stats.partial} color="#f59e0b" />
          <MiniStat label="Non-Compliant" value={stats.nonCompliant} color="#ef4444" />
          <MiniStat label="Not Assessed" value={stats.notAssessed} color="#94a3b8" />
        </div>

        {/* Progress bar */}
        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "16px 20px" }}>
          <div style={{ display: "flex", gap: 2, height: 12, borderRadius: 6, overflow: "hidden", background: "#e2e8f0" }}>
            {stats.compliant > 0 && <div style={{ width: `${(stats.compliant / stats.total) * 100}%`, background: "#10b981", transition: "width 0.3s" }} />}
            {stats.partial > 0 && <div style={{ width: `${(stats.partial / stats.total) * 100}%`, background: "#f59e0b", transition: "width 0.3s" }} />}
            {stats.nonCompliant > 0 && <div style={{ width: `${(stats.nonCompliant / stats.total) * 100}%`, background: "#ef4444", transition: "width 0.3s" }} />}
          </div>
          <div style={{ fontSize: 12, color: "#64748b", marginTop: 8, textAlign: "center" }}>
            {Math.round(((stats.compliant + stats.partial * 0.5) / stats.total) * 100)}% overall compliance score
          </div>
        </div>

        {/* Checklist by Category */}
        {categories.map((cat) => (
          <div key={cat} style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
            <button onClick={() => toggleSection(cat)} style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px", background: "#f8fafc", border: "none", cursor: "pointer", borderBottom: expandedSections[cat] ? "1px solid #e2e8f0" : "none" }}>
              <span style={{ fontWeight: 600, fontSize: 15, color: "#0f172a", fontFamily: "'Source Serif 4', Georgia, serif" }}>{cat}</span>
              <span style={{ color: "#94a3b8", transform: expandedSections[cat] ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }}>▼</span>
            </button>
            {expandedSections[cat] && (
              <div style={{ padding: "4px 0" }}>
                {GAP_ANALYSIS_ITEMS.filter((i) => i.category === cat).map((item) => (
                  <div key={item.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 20px", borderBottom: "1px solid #f1f5f9" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, color: "#0f172a", fontWeight: item.critical ? 500 : 400 }}>
                        {item.critical && <span style={{ color: "#ef4444", marginRight: 4 }} title="Critical requirement">●</span>}
                        {item.item}
                      </div>
                      <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>Clause {item.clause}</div>
                    </div>
                    <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
                      {["compliant", "partial", "non-compliant"].map((status) => (
                        <button key={status} onClick={() => setGapStatus(item.id, gapStatuses[item.id] === status ? null : status)} style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid ${gapStatuses[item.id] === status ? getStatusColor(status) : "#e2e8f0"}`, background: gapStatuses[item.id] === status ? getStatusColor(status) + "15" : "#fff", color: gapStatuses[item.id] === status ? getStatusColor(status) : "#94a3b8", fontSize: 11, fontWeight: 600, cursor: "pointer", transition: "all 0.15s", textTransform: "capitalize" }}>
                          {status === "non-compliant" ? "Gap" : status === "partial" ? "Partial" : "✓"}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderStandards = () => (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {/* ISO 13485 Deep Dive */}
      <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
        <h3 style={{ margin: "0 0 4px 0", fontSize: 20, fontWeight: 700, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>ISO 13485:2016 — Clause-Level Reference</h3>
        <p style={{ fontSize: 13, color: "#64748b", margin: "0 0 20px 0" }}>Quality management systems — Requirements for regulatory purposes</p>

        {ISO_13485_CLAUSES.map((section) => (
          <div key={section.id} style={{ marginBottom: 8 }}>
            <button onClick={() => toggleSection("iso-" + section.id)} style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", background: "#f0f4f8", border: "1px solid #e2e8f0", borderRadius: expandedSections["iso-" + section.id] ? "8px 8px 0 0" : 8, cursor: "pointer" }}>
              <span style={{ fontWeight: 600, fontSize: 14, color: "#0f172a" }}>
                <span style={{ color: "#3b82f6", marginRight: 8 }}>§{section.id}</span>
                {section.title}
              </span>
              <span style={{ color: "#94a3b8", transform: expandedSections["iso-" + section.id] ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s", fontSize: 12 }}>▼</span>
            </button>
            {expandedSections["iso-" + section.id] && (
              <div style={{ border: "1px solid #e2e8f0", borderTop: "none", borderRadius: "0 0 8px 8px", background: "#fff" }}>
                {section.subclauses.map((sub) => (
                  <div key={sub.id} style={{ padding: "12px 16px", borderBottom: "1px solid #f1f5f9" }}>
                    <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: "#3b82f6", minWidth: 42, fontFamily: "monospace" }}>{sub.id}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: "#0f172a" }}>
                          {sub.title}
                          {sub.critical && <span style={{ marginLeft: 6, background: "#fee2e2", color: "#dc2626", padding: "1px 6px", borderRadius: 4, fontSize: 10, fontWeight: 700 }}>CRITICAL</span>}
                        </div>
                        <div style={{ fontSize: 12, color: "#475569", marginTop: 4, lineHeight: 1.6 }}>{sub.summary}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Standards Reference Table */}
      <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
        <h3 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>Standards Reference Library</h3>
        {Object.entries(STANDARDS_MAP).map(([key, std]) => (
          <div key={key} style={{ padding: "14px 0", borderBottom: "1px solid #f1f5f9" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
              <div style={{ flex: 1, minWidth: 250 }}>
                <div style={{ fontWeight: 600, fontSize: 14, color: "#0f172a" }}>{key}</div>
                <div style={{ fontSize: 12, color: "#64748b" }}>{std.title}</div>
              </div>
              <span style={{ background: getCategoryColor(std.category), color: "#fff", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, textTransform: "uppercase" }}>{std.category}</span>
            </div>
            <div style={{ fontSize: 12, color: "#475569", marginTop: 6, lineHeight: 1.6 }}>{std.summary}</div>
            <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap", alignItems: "center" }}>
              <span style={{ fontSize: 11, color: "#94a3b8", marginRight: 4 }}>Markets:</span>
              {std.applicableMarkets.map((m) => (
                <span key={m} style={{ fontSize: 14 }} title={MARKETS[m]?.name}>{MARKETS[m]?.flag}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderChat = () => (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 200px)", minHeight: 500 }}>
      <div style={{ background: "#fff", borderRadius: "12px 12px 0 0", border: "1px solid #e2e8f0", borderBottom: "none", padding: "16px 20px" }}>
        <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, fontFamily: "'Source Serif 4', Georgia, serif", color: "#0f172a" }}>AI Regulatory Advisor</h3>
        <p style={{ fontSize: 12, color: "#64748b", margin: "4px 0 0 0" }}>Ask about regulatory requirements, testing, submission pathways, standards interpretation, and more. {productProfile.name && `Context: ${productProfile.name} profile is loaded.`}</p>
      </div>

      <div style={{ flex: 1, overflowY: "auto", background: "#f8fafc", border: "1px solid #e2e8f0", borderTop: "none", borderBottom: "none", padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
        {chatMessages.length === 0 && (
          <div style={{ textAlign: "center", padding: 40, color: "#94a3b8" }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>◎</div>
            <div style={{ fontSize: 14, fontWeight: 500, color: "#64748b" }}>Ask me anything about medical device regulations</div>
            <div style={{ fontSize: 12, marginTop: 8, maxWidth: 500, margin: "8px auto 0" }}>
              Try: "What biocompatibility testing do I need for a Class II skin-contact device in Brazil?" or "Compare the 510(k) pathway with EU MDR conformity assessment for a Class IIa device."
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginTop: 20 }}>
              {[
                "What are the key differences between FDA 510(k) and EU MDR for Class II?",
                "What does ANVISA require for GMP compliance?",
                "List all biocompatibility tests for prolonged mucosal contact",
                "Compare submission timelines across all my target markets",
              ].map((q, i) => (
                <button key={i} onClick={() => { setChatInput(q); }} style={{ padding: "8px 14px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", fontSize: 12, color: "#475569", cursor: "pointer", transition: "all 0.15s", maxWidth: 280, textAlign: "left" }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {chatMessages.map((msg, i) => (
          <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
            <div style={{ maxWidth: "80%", padding: "12px 16px", borderRadius: msg.role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px", background: msg.role === "user" ? "#1a2d50" : "#fff", color: msg.role === "user" ? "#fff" : "#0f172a", border: msg.role === "user" ? "none" : "1px solid #e2e8f0", fontSize: 13, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
              {msg.content}
            </div>
          </div>
        ))}
        {chatLoading && (
          <div style={{ display: "flex", justifyContent: "flex-start" }}>
            <div style={{ padding: "12px 16px", borderRadius: "12px 12px 12px 2px", background: "#fff", border: "1px solid #e2e8f0", color: "#94a3b8", fontSize: 13 }}>
              Analyzing regulatory requirements...
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div style={{ background: "#fff", borderRadius: "0 0 12px 12px", border: "1px solid #e2e8f0", borderTop: "none", padding: "12px 16px", display: "flex", gap: 10 }}>
        <input
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendChat()}
          placeholder="Ask about regulatory requirements, testing, pathways..."
          style={{ flex: 1, padding: "10px 14px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13, outline: "none", fontFamily: "inherit" }}
        />
        <button onClick={sendChat} disabled={chatLoading || !chatInput.trim()} style={{ padding: "10px 20px", borderRadius: 8, border: "none", background: chatLoading || !chatInput.trim() ? "#cbd5e1" : "#1a2d50", color: "#fff", fontWeight: 600, fontSize: 13, cursor: chatLoading ? "wait" : "pointer", transition: "all 0.15s" }}>
          Send
        </button>
      </div>
    </div>
  );

  // ═══════════════════════════════════════════════════════════════
  // MAIN RENDER
  // ═══════════════════════════════════════════════════════════════

  return (
    <div style={{ fontFamily: "'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif", background: "#f1f5f9", minHeight: "100vh" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Source+Serif+4:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet" />

      {/* Top Bar */}
      <div style={{ background: "#0a1628", padding: "0 24px", display: "flex", alignItems: "center", height: 56, gap: 12, borderBottom: "1px solid #1e3a5f" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 6, background: "linear-gradient(135deg, #38bdf8, #3b82f6)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 700, color: "#fff" }}>R</div>
          <span style={{ color: "#fff", fontWeight: 700, fontSize: 15, letterSpacing: "-0.01em", fontFamily: "'Source Serif 4', Georgia, serif" }}>RegIntel</span>
          <span style={{ color: "#475569", fontSize: 12, marginLeft: 4 }}>Medical Device Regulatory Intelligence</span>
        </div>
      </div>

      <div style={{ display: "flex", minHeight: "calc(100vh - 56px)" }}>
        {/* Sidebar */}
        <div style={{ width: 220, background: "#0f1d32", padding: "16px 0", flexShrink: 0, display: "flex", flexDirection: "column" }}>
          {TABS.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", border: "none", background: activeTab === tab.id ? "rgba(56,189,248,0.1)" : "transparent", color: activeTab === tab.id ? "#38bdf8" : "#94a3b8", cursor: "pointer", fontSize: 13, fontWeight: activeTab === tab.id ? 600 : 400, transition: "all 0.15s", textAlign: "left", borderLeft: activeTab === tab.id ? "3px solid #38bdf8" : "3px solid transparent", fontFamily: "inherit" }}>
              <span style={{ fontSize: 16, width: 20, textAlign: "center" }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}

          <div style={{ marginTop: "auto", padding: "16px 20px", borderTop: "1px solid #1e3a5f" }}>
            <div style={{ fontSize: 11, color: "#475569", lineHeight: 1.5 }}>
              ISO 13485 · FDA 21 CFR 820<br />
              EU MDR · UK MDR · ANVISA<br />
              COFEPRIS · INVIMA · ANMAT
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, padding: 24, overflowY: "auto", maxHeight: "calc(100vh - 56px)" }}>
          {activeTab === "dashboard" && renderDashboard()}
          {activeTab === "profile" && renderProductProfile()}
          {activeTab === "matrix" && renderRequirementsMatrix()}
          {activeTab === "gap" && renderGapAnalysis()}
          {activeTab === "standards" && renderStandards()}
          {activeTab === "chat" && renderChat()}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// REUSABLE SUB-COMPONENTS
// ═══════════════════════════════════════════════════════════════

function StatCard({ label, value, sublabel, accent }) {
  return (
    <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "18px 20px", borderLeft: `4px solid ${accent}` }}>
      <div style={{ fontSize: 12, color: "#64748b", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", marginTop: 4, fontFamily: "'Source Serif 4', Georgia, serif" }}>{value}</div>
      <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>{sublabel}</div>
    </div>
  );
}

function MiniStat({ label, value, color }) {
  return (
    <div style={{ background: "#fff", borderRadius: 10, border: "1px solid #e2e8f0", padding: "12px 16px", textAlign: "center" }}>
      <div style={{ fontSize: 24, fontWeight: 700, color, fontFamily: "'Source Serif 4', Georgia, serif" }}>{value}</div>
      <div style={{ fontSize: 11, color: "#64748b", marginTop: 2, fontWeight: 500 }}>{label}</div>
    </div>
  );
}

function ActionCard({ title, description, action, buttonLabel }) {
  return (
    <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "20px 22px", display: "flex", flexDirection: "column" }}>
      <h4 style={{ margin: "0 0 6px 0", fontSize: 15, fontWeight: 600, color: "#0f172a", fontFamily: "'Source Serif 4', Georgia, serif" }}>{title}</h4>
      <p style={{ fontSize: 13, color: "#64748b", margin: "0 0 14px 0", lineHeight: 1.5, flex: 1 }}>{description}</p>
      <button onClick={action} style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #1a2d50", background: "transparent", color: "#1a2d50", fontWeight: 600, fontSize: 12, cursor: "pointer", transition: "all 0.15s", alignSelf: "flex-start", fontFamily: "inherit" }}>
        {buttonLabel}
      </button>
    </div>
  );
}

function FormField({ label, value, onChange, placeholder, fullWidth, textarea }) {
  const style = { width: "100%", padding: "10px 12px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13, outline: "none", fontFamily: "inherit", background: "#fafafa", transition: "border-color 0.15s", resize: textarea ? "vertical" : "none" };
  return (
    <div style={{ gridColumn: fullWidth ? "1 / -1" : undefined }}>
      <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#374151", marginBottom: 4 }}>{label}</label>
      {textarea ? (
        <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} rows={3} style={style} />
      ) : (
        <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} style={style} />
      )}
    </div>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <div>
      <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#374151", marginBottom: 4 }}>{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13, outline: "none", fontFamily: "inherit", background: "#fafafa", cursor: "pointer" }}>
        {options.map((opt) => (
          <option key={opt.v} value={opt.v}>{opt.l}</option>
        ))}
      </select>
    </div>
  );
}

function ToggleField({ label, checked, onChange }) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", padding: "10px 12px", borderRadius: 8, border: `1px solid ${checked ? "#3b82f6" : "#e2e8f0"}`, background: checked ? "#eff6ff" : "#fafafa", transition: "all 0.15s" }}>
      <div onClick={(e) => { e.preventDefault(); onChange(!checked); }} style={{ width: 38, height: 22, borderRadius: 11, background: checked ? "#3b82f6" : "#cbd5e1", position: "relative", transition: "background 0.2s", cursor: "pointer", flexShrink: 0 }}>
        <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#fff", position: "absolute", top: 2, left: checked ? 18 : 2, transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 500, color: "#374151" }}>{label}</span>
    </label>
  );
}

// ── Utility Functions ──

const thStyle = {
  padding: "10px 14px",
  textAlign: "left",
  fontSize: 12,
  fontWeight: 600,
  color: "#64748b",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  borderBottom: "2px solid #e2e8f0",
};

const tdStyle = {
  padding: "10px 14px",
  fontSize: 13,
  color: "#374151",
  verticalAlign: "top",
};

function getCategoryColor(cat) {
  const colors = {
    QMS: "#3b82f6",
    "Risk Management": "#ef4444",
    Usability: "#8b5cf6",
    "Electrical Safety": "#f59e0b",
    Biocompatibility: "#10b981",
    Sterilization: "#06b6d4",
    Packaging: "#6366f1",
    Software: "#ec4899",
    Labeling: "#475569",
  };
  return colors[cat] || "#64748b";
}

function getStatusColor(status) {
  return status === "compliant" ? "#10b981" : status === "partial" ? "#f59e0b" : "#ef4444";
}
