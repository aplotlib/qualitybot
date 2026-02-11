# src/regulatory_data.py
# Complete regulatory knowledge base ported from regulatory-tool.jsx

MARKETS = {
    "US": {"name": "United States", "agency": "FDA", "flag": "\U0001f1fa\U0001f1f8", "color": "#1a4480"},
    "EU": {"name": "European Union", "agency": "EU MDR", "flag": "\U0001f1ea\U0001f1fa", "color": "#003399"},
    "UK": {"name": "United Kingdom", "agency": "MHRA", "flag": "\U0001f1ec\U0001f1e7", "color": "#c8102e"},
    "BR": {"name": "Brazil", "agency": "ANVISA", "flag": "\U0001f1e7\U0001f1f7", "color": "#009c3b"},
    "MX": {"name": "Mexico", "agency": "COFEPRIS", "flag": "\U0001f1f2\U0001f1fd", "color": "#006847"},
    "CO": {"name": "Colombia", "agency": "INVIMA", "flag": "\U0001f1e8\U0001f1f4", "color": "#fcd116"},
    "AR": {"name": "Argentina", "agency": "ANMAT", "flag": "\U0001f1e6\U0001f1f7", "color": "#74acdf"},
}

DEVICE_CLASSIFICATIONS = {
    "US": {
        "Class I": {
            "description": "Low risk devices, most exempt from 510(k)",
            "pathway": "510(k) exempt (most); some require 510(k)",
            "qsr": "21 CFR 820 (abbreviated for exempt devices)",
            "timeline": "N/A for exempt; 3-6 months for 510(k)",
            "establishment": "Establishment Registration + Device Listing required",
            "fees": "Annual establishment registration fee (~$7,653/yr FY2025)",
        },
        "Class II": {
            "description": "Moderate risk devices, most require 510(k)",
            "pathway": "510(k) Premarket Notification (most common); De Novo for novel devices",
            "qsr": "Full 21 CFR 820 Quality System Regulation compliance",
            "timeline": "510(k): 3-12 months; De Novo: 6-18 months",
            "establishment": "Establishment Registration + Device Listing required",
            "fees": "510(k) review fee (~$22,124 FY2025 for small business; ~$88,495 standard)",
        },
    },
    "EU": {
        "Class I": {
            "description": "Low risk, self-declaration with Notified Body for sterile/measuring",
            "pathway": "Self-certification (Annex II & III); NB required if sterile, measuring, or reusable surgical",
            "qsr": "Full EU MDR 2017/745 Annex I Essential Requirements + ISO 13485 QMS",
            "timeline": "6-12 months for technical documentation preparation",
            "establishment": "Authorized Representative required; EUDAMED registration",
            "fees": "Varies by Notified Body; AR fees EUR 5,000-15,000/yr",
        },
        "Class IIa": {
            "description": "Low-moderate risk, requires Notified Body certification",
            "pathway": "Conformity assessment via Notified Body (Annex IX or XI)",
            "qsr": "Full EU MDR 2017/745 compliance + ISO 13485 QMS + Technical Documentation per Annex II & III",
            "timeline": "12-18 months including NB audit",
            "establishment": "Authorized Representative required; EUDAMED registration; UDI-DI assignment",
            "fees": "NB certification EUR 15,000-50,000; annual surveillance EUR 10,000-25,000",
        },
        "Class IIb": {
            "description": "Medium-high risk, requires Notified Body with type examination",
            "pathway": "Conformity assessment via Notified Body (Annex IX + Annex X for implantables)",
            "qsr": "Full EU MDR 2017/745 + ISO 13485 + Clinical Evaluation per Annex XIV",
            "timeline": "18-24+ months",
            "establishment": "Authorized Representative required; EUDAMED registration; UDI-DI assignment",
            "fees": "NB certification EUR 30,000-80,000+; annual surveillance EUR 15,000-40,000",
        },
    },
    "UK": {
        "Class I": {
            "description": "Low risk, self-declaration under UK MDR 2002 (as amended)",
            "pathway": "Self-certification; UKCA marking (CE marking accepted until June 2030)",
            "qsr": "UK MDR 2002 + ISO 13485 QMS",
            "timeline": "3-6 months",
            "establishment": "MHRA device registration required; UK Responsible Person if non-UK manufacturer",
            "fees": "MHRA registration fees apply; UKRP fees vary",
        },
        "Class II": {
            "description": "Moderate risk, requires UK Approved Body",
            "pathway": "UKCA marking via UK Approved Body (CE accepted until June 2030 transition)",
            "qsr": "UK MDR 2002 + ISO 13485 QMS + Essential Requirements",
            "timeline": "12-18 months",
            "establishment": "MHRA registration; UK Responsible Person required",
            "fees": "Approved Body fees comparable to EU NB fees",
        },
    },
    "BR": {
        "Class I": {
            "description": "Low risk (Classe I under RDC 751/2022)",
            "pathway": "Cadastro (notification/registration) via ANVISA",
            "qsr": "RDC 665/2022 (GMP) + INMETRO certification for applicable products + Brazilian GMP (BGMP)",
            "timeline": "3-6 months for Cadastro",
            "establishment": "Brazilian Registration Holder (BRH) required; GMP certification",
            "fees": "Registration fees ~R$4,000-8,000; GMP inspection fees additional",
        },
        "Class II": {
            "description": "Moderate risk (Classe II under RDC 751/2022)",
            "pathway": "Registro (full registration) via ANVISA",
            "qsr": "RDC 665/2022 (GMP) + BGMP compliance + Technical documentation + Clinical evidence",
            "timeline": "12-24 months for Registro",
            "establishment": "Brazilian Registration Holder (BRH) required; GMP certification mandatory",
            "fees": "Registration fees ~R$8,000-25,000; GMP audit fees R$15,000-50,000+",
        },
    },
    "MX": {
        "Class I": {
            "description": "Low risk under COFEPRIS classification",
            "pathway": "Registro Sanitario (health registration) - simplified",
            "qsr": "NOM-241-SSA1-2021 (GMP) compliance; ISO 13485 recognized",
            "timeline": "3-6 months",
            "establishment": "Legal representative in Mexico required; Sanitary License (Licencia Sanitaria)",
            "fees": "Registration fees vary; legal representative costs $5,000-15,000/yr",
        },
        "Class II": {
            "description": "Moderate risk under COFEPRIS classification",
            "pathway": "Registro Sanitario with technical dossier review",
            "qsr": "NOM-241-SSA1-2021 (GMP) + Technical dossier with safety/efficacy data",
            "timeline": "6-18 months",
            "establishment": "Legal representative; Sanitary License; GMP compliance certificate",
            "fees": "Registration fees + technical review fees; third-party testing may be required",
        },
    },
    "CO": {
        "Class I": {
            "description": "Low risk (Clase I under Decreto 4725 de 2005)",
            "pathway": "Registro Sanitario via INVIMA - automatic/simplified",
            "qsr": "Decreto 4725 de 2005 + Resolucion 4002 de 2007 (GMP/BPE)",
            "timeline": "1-3 months for simplified registration",
            "establishment": "Colombian legal representative or importer required",
            "fees": "Registration fees ~COP 5-15 million",
        },
        "Class II": {
            "description": "Moderate risk (Clase IIa/IIb)",
            "pathway": "Registro Sanitario via INVIMA with technical evaluation",
            "qsr": "Decreto 4725 + GMP/BPE compliance + Technical documentation review",
            "timeline": "6-12 months",
            "establishment": "Colombian legal representative; Certificate of Free Sale from origin country",
            "fees": "Registration fees ~COP 15-40 million; evaluation fees additional",
        },
    },
    "AR": {
        "Class I": {
            "description": "Low risk (Clase I under Disposicion 2318/2002)",
            "pathway": "Registro de Producto Medico via ANMAT",
            "qsr": "Disposicion 2318/2002 + Disposicion 3266/2013 (GMP)",
            "timeline": "3-6 months",
            "establishment": "Argentine legal representative (Director Tecnico) required",
            "fees": "Registration fees ARS variable (subject to inflation adjustments)",
        },
        "Class II": {
            "description": "Moderate risk (Clase II)",
            "pathway": "Registro de Producto Medico via ANMAT with full technical review",
            "qsr": "Disposicion 2318/2002 + Full GMP compliance + Technical file + Risk management",
            "timeline": "6-18 months",
            "establishment": "Director Tecnico required; GMP certificate; Certificate of Free Sale",
            "fees": "Registration + technical review fees; GMP inspection costs",
        },
    },
}

ISO_13485_CLAUSES = [
    {
        "id": "4",
        "title": "Quality Management System",
        "subclauses": [
            {"id": "4.1", "title": "General Requirements", "summary": "Establish, document, implement, and maintain a QMS. Define processes, their sequence, interaction, criteria for effectiveness, resources, monitoring, and improvement. Outsourced processes must be controlled.", "critical": True},
            {"id": "4.1.1", "title": "General Requirements - Product Realization", "summary": "Document roles for provision, control of outsourced work, and risk management for each medical device."},
            {"id": "4.2", "title": "Documentation Requirements", "summary": "QMS documentation must include quality policy, quality objectives, quality manual, documented procedures, documents, and records required by this standard."},
            {"id": "4.2.1", "title": "General Documentation", "summary": "Documentation must address regulatory requirements and the organization's QMS needs."},
            {"id": "4.2.2", "title": "Quality Manual", "summary": "Establish and maintain a quality manual including scope, justified exclusions, documented procedures or references, and description of process interactions."},
            {"id": "4.2.3", "title": "Control of Documents", "summary": "Documented procedure to control documents: approval, review, updates, identification of changes, availability, legibility, identification of external documents, and prevention of obsolete document use.", "critical": True},
            {"id": "4.2.4", "title": "Control of Records", "summary": "Records must remain legible, readily identifiable, and retrievable. Documented procedure for identification, storage, security, integrity, retrieval, retention time, and disposition.", "critical": True},
            {"id": "4.2.5", "title": "Medical Device File", "summary": "For each medical device type or family, establish and maintain one or more files containing or referencing documents generated to demonstrate conformity and QMS effectiveness."},
        ],
    },
    {
        "id": "5",
        "title": "Management Responsibility",
        "subclauses": [
            {"id": "5.1", "title": "Management Commitment", "summary": "Top management must demonstrate commitment by communicating regulatory and customer importance, establishing quality policy and objectives, conducting management reviews, and ensuring resource availability."},
            {"id": "5.2", "title": "Customer Focus", "summary": "Ensure customer and applicable regulatory requirements are determined and met."},
            {"id": "5.3", "title": "Quality Policy", "summary": "Quality policy must be appropriate to purpose, include commitment to comply with requirements and maintain QMS effectiveness, and be communicated and understood."},
            {"id": "5.4", "title": "Planning", "summary": "Quality objectives must be established at relevant functions and levels. QMS planning must meet general requirements and quality objectives."},
            {"id": "5.5", "title": "Responsibility, Authority and Communication", "summary": "Define and communicate responsibilities and authorities. Appoint management representative. Establish internal communication processes."},
            {"id": "5.6", "title": "Management Review", "summary": "Review QMS at planned intervals for suitability, adequacy, and effectiveness. Include evaluation of improvement opportunities and need for changes. Maintain records of reviews.", "critical": True},
        ],
    },
    {
        "id": "6",
        "title": "Resource Management",
        "subclauses": [
            {"id": "6.1", "title": "Provision of Resources", "summary": "Determine and provide resources needed to implement and maintain QMS, meet regulatory and customer requirements."},
            {"id": "6.2", "title": "Human Resources", "summary": "Personnel performing QMS-affecting work must be competent based on education, training, skills, and experience. Determine competence, provide training, evaluate effectiveness, maintain records."},
            {"id": "6.3", "title": "Infrastructure", "summary": "Determine, provide, and maintain infrastructure needed for conformity: buildings, workspace, process equipment (hardware and software), supporting services. Document maintenance requirements including intervals."},
            {"id": "6.4", "title": "Work Environment and Contamination Control", "summary": "Determine and manage work environment needed for conformity. Document requirements for health, cleanliness, clothing if they could affect product quality. Establish contamination control arrangements as appropriate."},
        ],
    },
    {
        "id": "7",
        "title": "Product Realization",
        "subclauses": [
            {"id": "7.1", "title": "Planning of Product Realization", "summary": "Plan and develop processes needed for product realization consistent with QMS requirements. Determine quality objectives, need for processes and documentation, verification/validation/monitoring/testing, and records.", "critical": True},
            {"id": "7.2", "title": "Customer-Related Processes", "summary": "Determine product requirements including regulatory, delivery, and implied requirements. Review ability to meet requirements before commitment. Establish customer communication arrangements."},
            {"id": "7.3", "title": "Design and Development", "summary": "Establish documented procedures for design and development. Plan and control design stages including review, verification, and validation activities. Manage design inputs, outputs, reviews, verification, validation, transfer, changes, and design history files.", "critical": True},
            {"id": "7.3.2", "title": "Design and Development Planning", "summary": "Document design plans including stages, reviews/verifications/validations, responsibilities, methods for traceability of design outputs to inputs, and resources needed."},
            {"id": "7.3.3", "title": "Design and Development Inputs", "summary": "Determine and record inputs relating to functionality, performance, safety, regulatory requirements, risk management outputs, and applicable standards."},
            {"id": "7.3.4", "title": "Design and Development Outputs", "summary": "Outputs must be verifiable against inputs and approved before release. Must include acceptance criteria, essential characteristics for safe and proper use, and reference purchasing/production/servicing information."},
            {"id": "7.3.5", "title": "Design and Development Review", "summary": "Systematic reviews at suitable stages to evaluate ability to fulfill requirements and identify problems. Include representatives of functions concerned. Maintain records."},
            {"id": "7.3.6", "title": "Design and Development Verification", "summary": "Verification performed per planned arrangements to ensure outputs meet input requirements. Maintain records of verification results and actions."},
            {"id": "7.3.7", "title": "Design and Development Validation", "summary": "Validation under defined operating conditions per planned arrangements, including clinical evaluation or performance evaluation as applicable. Maintain records.", "critical": True},
            {"id": "7.3.8", "title": "Design and Development Transfer", "summary": "Document procedures for transfer of design outputs to manufacturing. Verify that outputs are suitable for manufacturing before becoming final production specifications."},
            {"id": "7.3.9", "title": "Control of Design and Development Changes", "summary": "Identify, document, review, verify, validate as appropriate, and approve design changes before implementation. Maintain records."},
            {"id": "7.3.10", "title": "Design and Development Files", "summary": "Maintain a design and development file for each medical device type or family."},
            {"id": "7.4", "title": "Purchasing", "summary": "Ensure purchased product conforms to requirements. Evaluate and select suppliers based on ability to supply. Establish criteria for evaluation, selection, monitoring, and re-evaluation. Maintain records.", "critical": True},
            {"id": "7.5", "title": "Production and Service Provision", "summary": "Plan and carry out production and service provision under controlled conditions. Validate processes where output cannot be verified by subsequent monitoring. Establish requirements for cleanliness and contamination control. Implement servicing activities and verify they meet requirements.", "critical": True},
            {"id": "7.5.1", "title": "Control of Production and Service Provision", "summary": "Controlled conditions include: documented procedures, infrastructure, process parameters and monitoring, measuring equipment, and defined operations for labeling, packaging, and release."},
            {"id": "7.5.2", "title": "Cleanliness of Product", "summary": "Document cleanliness requirements if product is cleaned before sterilization or its use, supplied non-sterile for sterilization, supplied as non-sterile but cleanliness is important, or agents are to be removed during manufacturing."},
            {"id": "7.5.4", "title": "Servicing Activities", "summary": "When servicing is a specified requirement, document servicing procedures, reference materials, and measuring requirements. Analyze servicing records for potential use as complaint handling data."},
            {"id": "7.5.6", "title": "Validation of Processes for Production and Service Provision", "summary": "Validate any process where the resulting output cannot be or is not verified by subsequent monitoring or measurement. This includes sterilization processes and aseptic processing.", "critical": True},
            {"id": "7.5.7", "title": "Particular Requirements for Validation of Processes for Sterilization and Sterile Barrier Systems", "summary": "Validate sterilization processes and sterile barrier system processes before implementation and after changes. Maintain records.", "critical": True},
            {"id": "7.5.8", "title": "Identification", "summary": "Identify product by suitable means throughout product realization. Identify product status with respect to monitoring and measurement requirements."},
            {"id": "7.5.9", "title": "Traceability", "summary": "Document procedures for traceability. For implantable devices, require records of all components, materials, and work environment conditions used. Require distribution records to allow investigation.", "critical": True},
            {"id": "7.6", "title": "Control of Monitoring and Measuring Equipment", "summary": "Determine monitoring and measurement needed. Establish documented procedures to ensure valid results. Calibrate or verify at specified intervals. Adjust as necessary. Identify calibration status. Safeguard from adjustments. Maintain calibration records.", "critical": True},
        ],
    },
    {
        "id": "8",
        "title": "Measurement, Analysis and Improvement",
        "subclauses": [
            {"id": "8.1", "title": "General", "summary": "Plan and implement monitoring, measurement, analysis, and improvement processes needed to demonstrate conformity, ensure QMS conformity, and maintain QMS effectiveness."},
            {"id": "8.2", "title": "Monitoring and Measurement", "summary": "Monitor information on whether customer requirements are met (feedback system). Implement complaint handling procedures. Report to regulatory authorities as required. Conduct internal audits at planned intervals. Monitor and measure QMS processes and product.", "critical": True},
            {"id": "8.2.1", "title": "Feedback", "summary": "Gather and monitor information on whether the organization has met customer requirements. This serves as one measurement of QMS effectiveness. Include feedback from production and post-production activities."},
            {"id": "8.2.2", "title": "Complaint Handling", "summary": "Document procedures for timely complaint handling per applicable regulatory requirements. Investigate all complaints. Determine if complaint is a reportable event. If complaint is not investigated, document justification.", "critical": True},
            {"id": "8.2.3", "title": "Reporting to Regulatory Authorities", "summary": "If regulatory requirements require notification of complaints meeting reporting criteria for adverse events or issuance of advisory notices, document procedures for reporting.", "critical": True},
            {"id": "8.2.4", "title": "Internal Audit", "summary": "Conduct internal audits at planned intervals. Document audit program, criteria, scope, frequency, methods. Ensure auditor objectivity and impartiality. Document procedure for planning, conducting, recording, and reporting audits.", "critical": True},
            {"id": "8.2.5", "title": "Monitoring and Measurement of Processes", "summary": "Apply suitable methods for monitoring and measurement of QMS processes. When planned results are not achieved, take correction and corrective action as appropriate."},
            {"id": "8.2.6", "title": "Monitoring and Measurement of Product", "summary": "Monitor and measure characteristics of product to verify product requirements are fulfilled. Maintain evidence of conformity with acceptance criteria. Record identity of person authorizing release.", "critical": True},
            {"id": "8.3", "title": "Control of Nonconforming Product", "summary": "Ensure nonconforming product is identified and controlled to prevent unintended use or delivery. Document procedure defining controls, responsibilities, and authorities. Take appropriate action to the effects of nonconformity. Maintain records.", "critical": True},
            {"id": "8.4", "title": "Analysis of Data", "summary": "Determine, collect, and analyze appropriate data to demonstrate QMS suitability, adequacy, and effectiveness. Include data from monitoring and measurement and other relevant sources (feedback, conformity, trends, suppliers, audits, service reports)."},
            {"id": "8.5", "title": "Improvement", "summary": "Identify and implement changes necessary to ensure and maintain QMS suitability, adequacy, and effectiveness. Implement corrective actions to eliminate causes of nonconformities. Implement preventive actions to eliminate causes of potential nonconformities.", "critical": True},
            {"id": "8.5.1", "title": "Corrective Action (CAPA)", "summary": "Document procedure for: reviewing nonconformities (including complaints), determining causes, evaluating need for action, planning and implementing action, recording results, and reviewing effectiveness of corrective action taken.", "critical": True},
            {"id": "8.5.2", "title": "Preventive Action", "summary": "Document procedure for: determining potential nonconformities and their causes, evaluating need for action, planning and implementing action, recording results, and reviewing effectiveness of preventive action taken.", "critical": True},
            {"id": "8.5.3", "title": "Advisory Notices and Recalls", "summary": "Document procedures for issuing advisory notices and implementing recalls in accordance with applicable regulatory requirements. Ability to issue at any time. Maintain records of investigation and recall actions.", "critical": True},
        ],
    },
]

STANDARDS_MAP = {
    "ISO 13485:2016": {
        "title": "Quality Management Systems - Requirements for Regulatory Purposes",
        "category": "QMS",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["all"],
        "summary": "Core QMS standard for medical devices. Required directly or recognized in all major markets. Covers design controls, production, CAPA, risk management integration, and regulatory compliance.",
    },
    "ISO 14971:2019": {
        "title": "Application of Risk Management to Medical Devices",
        "category": "Risk Management",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["all"],
        "summary": "Defines the risk management process for medical devices throughout the lifecycle. Required or recognized universally. Covers hazard identification, risk estimation, risk evaluation, risk control, and residual risk evaluation.",
    },
    "IEC 62366-1:2015+A1:2020": {
        "title": "Application of Usability Engineering to Medical Devices",
        "category": "Usability",
        "applicableMarkets": ["US", "EU", "UK", "BR"],
        "deviceTypes": ["all"],
        "summary": "Process for analyzing, specifying, developing, and evaluating usability of medical devices. Essential for user interface design, use-related risk analysis, formative and summative evaluations.",
    },
    "IEC 60601-1:2005+A1+A2": {
        "title": "General Requirements for Basic Safety and Essential Performance of Medical Electrical Equipment",
        "category": "Electrical Safety",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["electrical", "electronic", "software-driven"],
        "summary": "Fundamental safety standard for medical electrical equipment. Covers electrical safety, mechanical safety, radiation, temperature, accuracy, and essential performance.",
    },
    "ISO 10993 Series": {
        "title": "Biological Evaluation of Medical Devices",
        "category": "Biocompatibility",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["patient-contact", "implantable", "body-fluid-contact"],
        "summary": "Framework for biological evaluation of medical devices based on nature and duration of body contact. Part 1 defines evaluation/testing framework. Key parts: -3 (genotoxicity), -4 (blood interaction), -5 (cytotoxicity), -6 (implant effects), -10 (irritation/sensitization), -11 (systemic toxicity).",
    },
    "ISO 11135:2014": {
        "title": "Sterilization of Healthcare Products - Ethylene Oxide",
        "category": "Sterilization",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["sterile-EO"],
        "summary": "Requirements for development, validation, and routine control of EO sterilization process for medical devices.",
    },
    "ISO 11137 Series": {
        "title": "Sterilization of Healthcare Products - Radiation",
        "category": "Sterilization",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["sterile-radiation"],
        "summary": "Requirements for development, validation, and routine control of radiation sterilization (gamma, e-beam, X-ray).",
    },
    "ISO 11607-1/-2": {
        "title": "Packaging for Terminally Sterilized Medical Devices",
        "category": "Packaging",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["sterile"],
        "summary": "Requirements for materials, sterile barrier systems, and packaging systems for terminally sterilized medical devices. Part 1: requirements for materials. Part 2: validation of forming, sealing, and assembly processes.",
    },
    "IEC 62304:2006+A1:2015": {
        "title": "Medical Device Software - Software Life Cycle Processes",
        "category": "Software",
        "applicableMarkets": ["US", "EU", "UK", "BR"],
        "deviceTypes": ["software", "software-driven"],
        "summary": "Framework for lifecycle processes for medical device software development and maintenance. Defines software safety classification and corresponding requirements for planning, analysis, design, implementation, testing, and maintenance.",
    },
    "ISO 15223-1:2021": {
        "title": "Symbols to be Used with Information Supplied by the Manufacturer",
        "category": "Labeling",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["all"],
        "summary": "Standardized symbols for use on medical device labels, labeling, and information supplied by the manufacturer.",
    },
    "EN 556-1:2001": {
        "title": "Requirements for Terminally Sterilized Devices to be Labeled STERILE",
        "category": "Sterilization",
        "applicableMarkets": ["EU", "UK"],
        "deviceTypes": ["sterile"],
        "summary": "Specifies requirements to be met in order for a terminally sterilized medical device to bear the label STERILE and SAL of 10^-6.",
    },
    "ISO 20417:2021": {
        "title": "Information to be Supplied by the Manufacturer",
        "category": "Labeling",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["all"],
        "summary": "General requirements for information to be supplied with medical devices: labels, instructions for use, technical descriptions.",
    },
    "ISO 10535:2021": {
        "title": "Assistive Products - Hoists for the Transfer of Persons - Requirements and Test Methods",
        "category": "Assistive Devices",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["assistive", "mobility", "transfer-hoist"],
        "summary": "Requirements and test methods for hoists (mobile, stationary, pool) and body-support units (slings) for transferring persons with disability. Covers safety, durability (10,000 cycles), static strength (1.5x SWL), stability, ergonomics, and labelling. FDA Class II (21 CFR 890.3480); EU MDR Class I (manual) or Class IIa (powered).",
    },
    "ISO 80002-2:2017": {
        "title": "Medical Device Software - Part 2: Validation of Software for Medical Device Quality Systems",
        "category": "Software",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["all"],
        "summary": "Guidance on validation of software used in the medical device QMS (ERP, MES, LIMS, document management, etc.). Defines risk-based validation approach using GAMP categories. Required by ISO 13485:2016 Clause 4.1.6 and FDA 21 CFR 820.70(i). Covers IQ/OQ/PQ, change control, periodic review, and 21 CFR Part 11 compliance.",
    },
    "ISO 11199-3:2005": {
        "title": "Walking Aids Manipulated by Both Arms - Part 3: Walking Tables",
        "category": "Assistive Devices",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["assistive", "mobility", "walking-aid"],
        "summary": "Requirements and test methods for walking tables (wheeled walking aids with forearm supports). Covers static strength (1.5x SWL), stability, fatigue (200,000 cycles), braking, rolling resistance, sharp edges, and labelling. FDA Class I (21 CFR 890.3420, 510(k) exempt); EU MDR Class I.",
    },
    "ISO 3758:2023": {
        "title": "Textiles - Care Labelling Code Using Symbols",
        "category": "Labeling",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["textile", "reusable", "slings", "garments"],
        "summary": "Standardized care labelling symbols for textile articles (washing, bleaching, drying, ironing, professional care). Relevant for medical textiles, reusable device components (slings, straps, covers), and reprocessing instructions. Must align with ISO 17664 for reusable medical devices.",
    },
    "ISO 27427:2023": {
        "title": "Anaesthetic and Respiratory Equipment - Nebulizing Systems and Components",
        "category": "Respiratory Equipment",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["respiratory", "nebulizer", "drug-delivery"],
        "summary": "Requirements for nebulizer systems (jet, ultrasonic, mesh/membrane) including performance (MMAD, FPF, output rate), safety, biocompatibility, electrical safety, and labelling. FDA Class II (21 CFR 868.5630, 510(k) required); EU MDR Class IIa. Covers reprocessing for reusable nebulizers.",
    },
    "ISO 17510:2015": {
        "title": "Medical Devices - Sleep Apnoea Breathing Therapy - Masks and Application Accessories",
        "category": "Respiratory Equipment",
        "applicableMarkets": ["US", "EU", "UK", "BR", "MX", "CO", "AR"],
        "deviceTypes": ["respiratory", "sleep-therapy", "CPAP-mask"],
        "summary": "Requirements for sleep apnoea masks (nasal, oronasal, nasal pillows) and accessories. Covers anti-asphyxia protection, CO2 washout, quick-release (<5s), dead space limits, breathing resistance, noise, biocompatibility, and durability. FDA Class II (21 CFR 868.5905, 510(k) required); EU MDR Class IIa.",
    },
}

TESTING_REQUIREMENTS = {
    "patient-contact": {
        "biocompatibility": {
            "title": "Biocompatibility Testing (ISO 10993)",
            "tests": [
                {"name": "Cytotoxicity (ISO 10993-5)", "required": "all", "duration": "2-4 weeks"},
                {"name": "Sensitization (ISO 10993-10)", "required": "all", "duration": "4-8 weeks"},
                {"name": "Irritation (ISO 10993-10/23)", "required": "all", "duration": "2-6 weeks"},
                {"name": "Systemic Toxicity (ISO 10993-11)", "required": "prolonged+permanent", "duration": "4-12 weeks"},
                {"name": "Genotoxicity (ISO 10993-3)", "required": "prolonged+permanent", "duration": "6-12 weeks"},
                {"name": "Implantation (ISO 10993-6)", "required": "implantable", "duration": "12-26 weeks"},
                {"name": "Hemocompatibility (ISO 10993-4)", "required": "blood-contact", "duration": "4-8 weeks"},
            ],
        },
    },
    "electrical": {
        "safety": {
            "title": "Electrical Safety Testing (IEC 60601-1)",
            "tests": [
                {"name": "Electrical Safety - General (60601-1)", "required": "all-electrical", "duration": "4-8 weeks"},
                {"name": "EMC Testing (IEC 60601-1-2)", "required": "all-electrical", "duration": "4-8 weeks"},
                {"name": "Software Safety Classification (IEC 62304)", "required": "software-driven", "duration": "N/A - process"},
                {"name": "Usability Engineering (IEC 62366-1)", "required": "all", "duration": "8-16 weeks"},
                {"name": "Alarm Systems (IEC 60601-1-8)", "required": "alarm-equipped", "duration": "2-4 weeks"},
            ],
        },
    },
    "sterile": {
        "sterilization": {
            "title": "Sterilization Validation",
            "tests": [
                {"name": "Bioburden Testing (ISO 11737-1)", "required": "all-sterile", "duration": "2-4 weeks"},
                {"name": "Sterility Testing (ISO 11737-2)", "required": "all-sterile", "duration": "2-4 weeks"},
                {"name": "EO Sterilization Validation (ISO 11135)", "required": "EO-sterilized", "duration": "8-16 weeks"},
                {"name": "Radiation Sterilization Validation (ISO 11137)", "required": "radiation-sterilized", "duration": "8-12 weeks"},
                {"name": "Packaging Validation (ISO 11607)", "required": "all-sterile", "duration": "4-12 weeks"},
                {"name": "Accelerated Aging / Shelf Life (ASTM F1980)", "required": "all-sterile", "duration": "8-16 weeks"},
                {"name": "Package Integrity - Seal Strength (ASTM F88)", "required": "all-sterile", "duration": "1-2 weeks"},
                {"name": "Package Integrity - Dye Penetration / Bubble (ASTM F1929/F2095)", "required": "all-sterile", "duration": "1-2 weeks"},
            ],
        },
    },
    "general": {
        "design": {
            "title": "General Design & Performance",
            "tests": [
                {"name": "Risk Management File (ISO 14971)", "required": "all", "duration": "Ongoing - lifecycle"},
                {"name": "Essential Performance Testing", "required": "all", "duration": "4-12 weeks"},
                {"name": "Labeling Review (ISO 15223-1 / 21 CFR 801)", "required": "all", "duration": "2-4 weeks"},
                {"name": "Shelf Life / Stability Testing", "required": "all", "duration": "Real-time or accelerated"},
                {"name": "Transportation / Distribution Simulation (ISTA/ASTM D4169)", "required": "shipped-products", "duration": "2-4 weeks"},
                {"name": "Clinical Evaluation / Literature Review", "required": "all", "duration": "4-16 weeks"},
            ],
        },
    },
}

GAP_ANALYSIS_ITEMS = [
    {"id": "qms-1", "category": "QMS Foundation", "item": "Quality Manual documented and current", "clause": "4.2.2", "critical": True},
    {"id": "qms-2", "category": "QMS Foundation", "item": "Quality Policy established, communicated, understood", "clause": "5.3", "critical": True},
    {"id": "qms-3", "category": "QMS Foundation", "item": "Quality Objectives defined at relevant functions/levels", "clause": "5.4.1", "critical": False},
    {"id": "qms-4", "category": "QMS Foundation", "item": "Document control procedure implemented", "clause": "4.2.3", "critical": True},
    {"id": "qms-5", "category": "QMS Foundation", "item": "Record control procedure implemented", "clause": "4.2.4", "critical": True},
    {"id": "qms-6", "category": "QMS Foundation", "item": "Medical Device File(s) established per device family", "clause": "4.2.5", "critical": True},
    {"id": "mgmt-1", "category": "Management", "item": "Management Representative appointed", "clause": "5.5.2", "critical": True},
    {"id": "mgmt-2", "category": "Management", "item": "Management Reviews conducted at planned intervals with required inputs/outputs", "clause": "5.6", "critical": True},
    {"id": "mgmt-3", "category": "Management", "item": "Internal communication processes established", "clause": "5.5.3", "critical": False},
    {"id": "res-1", "category": "Resources", "item": "Competence requirements defined for QMS-affecting personnel", "clause": "6.2", "critical": True},
    {"id": "res-2", "category": "Resources", "item": "Training effectiveness evaluated and records maintained", "clause": "6.2", "critical": True},
    {"id": "res-3", "category": "Resources", "item": "Infrastructure documented with maintenance requirements/intervals", "clause": "6.3", "critical": False},
    {"id": "res-4", "category": "Resources", "item": "Work environment requirements documented (cleanliness, contamination control)", "clause": "6.4", "critical": False},
    {"id": "dc-1", "category": "Design Controls", "item": "Design and Development procedure documented", "clause": "7.3.1", "critical": True},
    {"id": "dc-2", "category": "Design Controls", "item": "Design Plan with stages, reviews, V&V activities, responsibilities", "clause": "7.3.2", "critical": True},
    {"id": "dc-3", "category": "Design Controls", "item": "Design Inputs documented (functional, performance, safety, regulatory, risk)", "clause": "7.3.3", "critical": True},
    {"id": "dc-4", "category": "Design Controls", "item": "Design Outputs meet input requirements and include acceptance criteria", "clause": "7.3.4", "critical": True},
    {"id": "dc-5", "category": "Design Controls", "item": "Design Reviews conducted at suitable stages with records", "clause": "7.3.5", "critical": True},
    {"id": "dc-6", "category": "Design Controls", "item": "Design Verification performed and recorded", "clause": "7.3.6", "critical": True},
    {"id": "dc-7", "category": "Design Controls", "item": "Design Validation performed under defined operating conditions", "clause": "7.3.7", "critical": True},
    {"id": "dc-8", "category": "Design Controls", "item": "Design Transfer procedure documented and executed", "clause": "7.3.8", "critical": True},
    {"id": "dc-9", "category": "Design Controls", "item": "Design Change control procedure implemented", "clause": "7.3.9", "critical": True},
    {"id": "dc-10", "category": "Design Controls", "item": "Design History File (DHF) maintained per device", "clause": "7.3.10", "critical": True},
    {"id": "pur-1", "category": "Purchasing", "item": "Supplier evaluation and selection criteria documented", "clause": "7.4.1", "critical": True},
    {"id": "pur-2", "category": "Purchasing", "item": "Approved Supplier List maintained with monitoring/re-evaluation", "clause": "7.4.1", "critical": True},
    {"id": "pur-3", "category": "Purchasing", "item": "Purchasing data specifies requirements adequately", "clause": "7.4.2", "critical": False},
    {"id": "pur-4", "category": "Purchasing", "item": "Incoming inspection/verification procedures established", "clause": "7.4.3", "critical": True},
    {"id": "prod-1", "category": "Production", "item": "Production procedures/work instructions documented", "clause": "7.5.1", "critical": True},
    {"id": "prod-2", "category": "Production", "item": "Process validation performed for special processes", "clause": "7.5.6", "critical": True},
    {"id": "prod-3", "category": "Production", "item": "Sterilization process validation (if applicable)", "clause": "7.5.7", "critical": True},
    {"id": "prod-4", "category": "Production", "item": "Product identification throughout realization", "clause": "7.5.8", "critical": True},
    {"id": "prod-5", "category": "Production", "item": "Traceability system implemented (especially for implantables)", "clause": "7.5.9", "critical": True},
    {"id": "prod-6", "category": "Production", "item": "Calibration program for monitoring/measuring equipment", "clause": "7.6", "critical": True},
    {"id": "prod-7", "category": "Production", "item": "Cleanliness requirements documented (if applicable)", "clause": "7.5.2", "critical": False},
    {"id": "fb-1", "category": "Feedback & Improvement", "item": "Customer feedback / post-market surveillance system", "clause": "8.2.1", "critical": True},
    {"id": "fb-2", "category": "Feedback & Improvement", "item": "Complaint handling procedure documented and implemented", "clause": "8.2.2", "critical": True},
    {"id": "fb-3", "category": "Feedback & Improvement", "item": "Regulatory reporting procedures (MDR, MedWatch, vigilance)", "clause": "8.2.3", "critical": True},
    {"id": "fb-4", "category": "Feedback & Improvement", "item": "Internal audit program planned and executed", "clause": "8.2.4", "critical": True},
    {"id": "fb-5", "category": "Feedback & Improvement", "item": "Nonconforming product control procedure", "clause": "8.3", "critical": True},
    {"id": "fb-6", "category": "Feedback & Improvement", "item": "CAPA (Corrective Action) procedure implemented", "clause": "8.5.1", "critical": True},
    {"id": "fb-7", "category": "Feedback & Improvement", "item": "CAPA (Preventive Action) procedure implemented", "clause": "8.5.2", "critical": True},
    {"id": "fb-8", "category": "Feedback & Improvement", "item": "Advisory notice / recall procedure documented", "clause": "8.5.3", "critical": True},
    {"id": "fb-9", "category": "Feedback & Improvement", "item": "Data analysis performed on QMS data (trends, suppliers, processes)", "clause": "8.4", "critical": False},
]

CATEGORY_COLORS = {
    "QMS": "#3b82f6",
    "Risk Management": "#ef4444",
    "Usability": "#8b5cf6",
    "Electrical Safety": "#f59e0b",
    "Biocompatibility": "#10b981",
    "Sterilization": "#06b6d4",
    "Packaging": "#6366f1",
    "Software": "#ec4899",
    "Labeling": "#475569",
    "Assistive Devices": "#14b8a6",
    "Respiratory Equipment": "#f97316",
    "Audit": "#6d28d9",
}


def get_applicable_standards(target_markets):
    """Filter standards by target markets."""
    if not target_markets:
        return list(STANDARDS_MAP.items())
    return [
        (key, std) for key, std in STANDARDS_MAP.items()
        if any(m in std["applicableMarkets"] for m in target_markets)
    ]


def get_applicable_tests(profile):
    """Get applicable tests based on product profile."""
    tests = []
    tests.extend(TESTING_REQUIREMENTS["general"]["design"]["tests"])
    if profile.get("contact_type") and profile["contact_type"] != "none":
        tests.extend(TESTING_REQUIREMENTS["patient-contact"]["biocompatibility"]["tests"])
    if profile.get("is_electrical") or profile.get("has_software"):
        tests.extend(TESTING_REQUIREMENTS["electrical"]["safety"]["tests"])
    if profile.get("sterile"):
        tests.extend(TESTING_REQUIREMENTS["sterile"]["sterilization"]["tests"])
    return tests


def get_gap_stats(gap_statuses):
    """Calculate gap analysis statistics."""
    total = len(GAP_ANALYSIS_ITEMS)
    compliant = sum(1 for s in gap_statuses.values() if s == "compliant")
    partial = sum(1 for s in gap_statuses.values() if s == "partial")
    non_compliant = sum(1 for s in gap_statuses.values() if s == "non-compliant")
    not_assessed = total - compliant - partial - non_compliant
    score = round(((compliant + partial * 0.5) / total) * 100) if total > 0 else 0
    return {
        "total": total,
        "compliant": compliant,
        "partial": partial,
        "non_compliant": non_compliant,
        "not_assessed": not_assessed,
        "score": score,
    }


def get_classification_info(market_code, profile):
    """Get device classification info for a specific market."""
    if market_code == "EU":
        class_key = profile.get("class_eu") or "Class IIa"
    else:
        raw = profile.get("class_us", "")
        if "Class II" in raw:
            class_key = "Class II"
        elif "Class I" in raw:
            class_key = "Class I"
        else:
            class_key = "Class II"

    market_classes = DEVICE_CLASSIFICATIONS.get(market_code, {})
    return market_classes.get(class_key) or market_classes.get("Class II") or market_classes.get("Class I")


def build_system_prompt(profile, gap_statuses):
    """Build the AI advisor system prompt with product context and full standards knowledge."""
    from src.standards_knowledge import build_knowledge_context, FDA_AUDIT_CHECKLIST

    profile_str = ""
    if profile.get("name"):
        profile_str = f"""

Current Product Profile:
- Name: {profile['name']}
- Description: {profile.get('description', '')}
- US Classification: {profile.get('class_us', '')}
- EU Classification: {profile.get('class_eu', '')}
- Target Markets: {', '.join(profile.get('target_markets', []))}
- Patient Contact: {profile.get('contact_type', '')} ({profile.get('contact_duration', '')})
- Sterile: {'Yes (' + profile.get('sterilization_method', '') + ')' if profile.get('sterile') else 'No'}
- Software: {'Yes (Class ' + profile.get('software_safety_class', '') + ')' if profile.get('has_software') else 'No'}
- Electrical: {'Yes' if profile.get('is_electrical') else 'No'}
- Implantable: {'Yes' if profile.get('is_implantable') else 'No'}
- Intended Use: {profile.get('intended_use', '')}
- Predicate Device: {profile.get('predicate_device', '')}"""

    gap_stats = get_gap_stats(gap_statuses)
    gap_str = ""
    if gap_stats["compliant"] + gap_stats["partial"] + gap_stats["non_compliant"] > 0:
        gap_str = f"""

Gap Analysis Status: {gap_stats['compliant']} compliant, {gap_stats['partial']} partial, {gap_stats['non_compliant']} non-compliant, {gap_stats['not_assessed']} not assessed out of {gap_stats['total']} items."""

    # Build knowledge context from integrated standards
    knowledge_context = build_knowledge_context()

    return f"""You are a world-class medical device regulatory expert assistant. You have deep expertise in:
- ISO 13485:2016 (Quality Management Systems)
- FDA 21 CFR 820 (Quality System Regulation) and 510(k)/De Novo pathways
- EU MDR 2017/745 (European Medical Device Regulation)
- UK MDR 2002 (as amended) and UKCA marking
- ANVISA (Brazil) - RDC 751/2022, RDC 665/2022
- COFEPRIS (Mexico) - NOM-241-SSA1-2021
- INVIMA (Colombia) - Decreto 4725 de 2005
- ANMAT (Argentina) - Disposicion 2318/2002
- ISO 14971 (Risk Management), IEC 60601-1 (Electrical Safety), ISO 10993 (Biocompatibility), IEC 62304 (Software), IEC 62366 (Usability), ISO 11607 (Packaging), ISO 11135/11137 (Sterilization)

You also have full access to the following integrated standards and reference documents:
- ISO 10535:2021 (Hoists for Transfer of Persons - requirements, test methods, safety)
- ISO 80002-2:2017 (Medical Device Software - QMS software validation, GAMP categories, IQ/OQ/PQ)
- ISO 11199-3:2005 (Walking Aids - Walking Tables - requirements and test methods)
- ISO 3758:2023 (Textiles Care Labelling - symbols for washing, bleaching, drying, ironing)
- ISO 27427:2023 (Nebulizing Systems - performance, safety, biocompatibility, test methods)
- ISO 17510:2015 (Sleep Apnoea Masks - anti-asphyxia, CO2 washout, dead space, quick-release)
- FDA QSR/QMSR/ISO 13485:2016 Internal Audit Checklist (169 items across all QMS subsystems)

You provide precise, actionable regulatory guidance. When discussing requirements, always specify the applicable regulation, clause, or standard. Compare market-specific requirements when relevant. Be direct and practical - the user is a quality management professional at a medical device company working with Class I and Class II devices.
{profile_str}{gap_str}

When the user asks about requirements for a specific market or product type, structure your response by market, listing the specific regulatory requirements, applicable standards, testing needed, and submission pathway. Always mention timelines and costs where possible.

When asked about any of the integrated standards above, draw from your detailed knowledge of their scope, requirements, test methods, classification, and regulatory context.

When asked about internal audits or audit checklists, reference the FDA QSR/QMSR/ISO 13485 audit checklist with specific item numbers, ISO references, and auditor notes.

--- INTEGRATED STANDARDS KNOWLEDGE BASE ---
{knowledge_context}"""
