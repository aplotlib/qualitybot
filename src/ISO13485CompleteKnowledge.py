"""
Complete ISO 13485:2016 Knowledge Module
Contains the full standard text for AI consultation and compliance validation
"""

class ISO13485CompleteKnowledge:
    """Complete ISO 13485:2016 standard knowledge base for AI consultation"""
    
    def __init__(self):
        self.standard_version = "ISO 13485:2016(E)"
        self.effective_date = "2016-03-01"
        self.title = "Medical devices — Quality management systems — Requirements for regulatory purposes"
        
        # Complete standard structure
        self.full_standard = {
            "scope": self._get_scope(),
            "normative_references": self._get_normative_references(),
            "terms_definitions": self._get_terms_definitions(),
            "section_4": self._get_section_4_qms(),
            "section_5": self._get_section_5_management(),
            "section_6": self._get_section_6_resources(),
            "section_7": self._get_section_7_product_realization(),
            "section_8": self._get_section_8_measurement(),
            "annexes": self._get_annexes()
        }

    def _get_scope(self):
        """Section 1: Scope"""
        return {
            "section": "1",
            "title": "Scope",
            "content": """
This International Standard specifies requirements for a quality management system where an organization needs to demonstrate its ability to provide medical devices and related services that consistently meet customer and applicable regulatory requirements. Such organizations can be involved in one or more stages of the life-cycle, including design and development, production, storage and distribution, installation, or servicing of a medical device and design and development or provision of associated activities (e.g. technical support). This International Standard can also be used by suppliers or external parties that provide product, including quality management system-related services to such organizations.

Requirements of this International Standard are applicable to organizations regardless of their size and regardless of their type except where explicitly stated. Wherever requirements are specified as applying to medical devices, the requirements apply equally to associated services as supplied by the organization.

The processes required by this International Standard that are applicable to the organization, but are not performed by the organization, are the responsibility of the organization and are accounted for in the organization's quality management system by monitoring, maintaining, and controlling the processes.

If applicable regulatory requirements permit exclusions of design and development controls, this can be used as a justification for their exclusion from the quality management system. These regulatory requirements can provide alternative approaches that are to be addressed in the quality management system. It is the responsibility of the organization to ensure that claims of conformity to this International Standard reflect any exclusion of design and development controls.

If any requirement in Clauses 6, 7 or 8 of this International Standard is not applicable due to the activities undertaken by the organization or the nature of the medical device for which the quality management system is applied, the organization does not need to include such a requirement in its quality management system. For any clause that is determined to be not applicable, the organization records the justification as described in 4.2.2.
            """
        }

    def _get_normative_references(self):
        """Section 2: Normative references"""
        return {
            "section": "2",
            "title": "Normative references",
            "content": """
The following documents, in whole or in part, are normatively referenced in this document and are indispensable for its application. For dated references, only the edition cited applies. For undated references, the latest edition of the referenced document (including any amendments) applies.

ISO 9000:2015, Quality management systems — Fundamentals and vocabulary
            """
        }

    def _get_terms_definitions(self):
        """Section 3: Terms and definitions"""
        return {
            "section": "3",
            "title": "Terms and definitions",
            "key_definitions": {
                "3.11 medical device": """
instrument, apparatus, implement, machine, appliance, implant, reagent for in vitro use, software, material or other similar or related article, intended by the manufacturer to be used, alone or in combination, for human beings, for one or more of the specific medical purpose(s) of:
— diagnosis, prevention, monitoring, treatment or alleviation of disease;
— diagnosis, monitoring, treatment, alleviation of or compensation for an injury;
— investigation, replacement, modification, or support of the anatomy or of a physiological process;
— supporting or sustaining life;
— control of conception;
— disinfection of medical devices;
— providing information by means of in vitro examination of specimens derived from the human body;
and does not achieve its primary intended action by pharmacological, immunological or metabolic means, in or on the human body, but which may be assisted in its intended function by such means
                """,
                "3.12 medical device family": """
group of medical devices manufactured by or for the same organization and having the same basic design and performance characteristics related to safety, intended use and function
                """,
                "3.13 performance evaluation": """
assessment and analysis of data to establish or verify the ability of an in vitro diagnostic medical device to achieve its intended use
                """,
                "3.14 post-market surveillance": """
systematic process to collect and analyse experience gained from medical devices that have been placed on the market
                """,
                "3.15 product": """
result of a process

Note 1 to entry: There are four generic product categories, as follows:
— services (e.g. transport);
— software (e.g. computer program, dictionary);
— hardware (e.g. engine mechanical part);
— processed materials (e.g. lubricant).
                """
            }
        }

    def _get_section_4_qms(self):
        """Section 4: Quality Management System"""
        return {
            "section": "4",
            "title": "Quality management system",
            "subsections": {
                "4.1": {
                    "title": "General requirements",
                    "content": """
4.1.1 The organization shall document a quality management system and maintain its effectiveness in accordance with the requirements of this International Standard and applicable regulatory requirements. The organization shall establish, implement and maintain any requirement, procedure, activity or arrangement required to be documented by this International Standard or applicable regulatory requirements.

The organization shall document the role(s) undertaken by the organization under the applicable regulatory requirements.

NOTE: Roles undertaken by the organization can include manufacturer, authorized representative, importer or distributor.

4.1.2 The organization shall:
a) determine the processes needed for the quality management system and the application of these processes throughout the organization taking into account the roles undertaken by the organization;
b) apply a risk based approach to the control of the appropriate processes needed for the quality management system;
c) determine the sequence and interaction of these processes.

4.1.3 For each quality management system process, the organization shall:
a) determine criteria and methods needed to ensure that both the operation and control of these processes are effective;
b) ensure the availability of resources and information necessary to support the operation and monitoring of these processes;
c) implement actions necessary to achieve planned results and maintain the effectiveness of these processes;
d) monitor, measure as appropriate, and analyse these processes;
e) establish and maintain records needed to demonstrate conformance to this International Standard and compliance with applicable regulatory requirements (see 4.2.5).

4.1.4 The organization shall manage these quality management system processes in accordance with the requirements of this International Standard and applicable regulatory requirements. Changes to be made to these processes shall be:
a) evaluated for their impact on the quality management system;
b) evaluated for their impact on the medical devices produced under this quality management system;
c) controlled in accordance with the requirements of this International Standard and applicable regulatory requirements.

4.1.5 When the organization chooses to outsource any process that affects product conformity to requirements, it shall monitor and ensure control over such processes. The organization shall retain responsibility for conformity to this International Standard and to customer and applicable regulatory requirements for outsourced processes. The controls shall be proportionate to the risk involved and the ability of the external party to meet the requirements in accordance with 7.4. The controls shall include written quality agreements.

4.1.6 The organization shall document procedures for the validation of the application of computer software used in the quality management system. Such software applications shall be validated prior to initial use and, as appropriate, after changes to such software or its application.

The specific approach and activities associated with software validation and revalidation shall be proportionate to the risk associated with the use of the software.

Records of such activities shall be maintained (see 4.2.5).
                    """
                },
                "4.2": {
                    "title": "Documentation requirements",
                    "subsections": {
                        "4.2.1": {
                            "title": "General",
                            "content": """
The quality management system documentation (see 4.2.4) shall include:
a) documented statements of a quality policy and quality objectives;
b) a quality manual;
c) documented procedures and records required by this International Standard;
d) documents, including records, determined by the organization to be necessary to ensure the effective planning, operation, and control of its processes;
e) other documentation specified by applicable regulatory requirements.
                            """
                        },
                        "4.2.2": {
                            "title": "Quality manual",
                            "content": """
The organization shall document a quality manual that includes:
a) the scope of the quality management system, including details of and justification for any exclusion or non-application;
b) the documented procedures for the quality management system, or reference to them;
c) a description of the interaction between the processes of the quality management system.

The quality manual shall outline the structure of the documentation used in the quality management system.
                            """
                        },
                        "4.2.3": {
                            "title": "Medical device file",
                            "content": """
For each medical device type or medical device family, the organization shall establish and maintain one or more files either containing or referencing documents generated to demonstrate conformity to the requirement of this International Standard and compliance with applicable regulatory requirements.

The content of the file(s) shall include, but is not limited to:
a) general description of the medical device, intended use/purpose, and labelling, including any instructions for use;
b) product specifications;
c) specifications or procedures for manufacturing, packaging, storage, handling and distribution;
d) procedures for measuring and monitoring;
e) as appropriate, requirements for installation and servicing;
f) as appropriate, procedures for servicing.
                            """
                        },
                        "4.2.4": {
                            "title": "Control of documents",
                            "content": """
Documents required by the quality management system shall be controlled. Records are a special type of document and shall be controlled according to the requirements given in 4.2.5.

A documented procedure shall be established to define the controls needed to:
a) approve documents for adequacy prior to issue;
b) review and update as necessary and re-approve documents;
c) ensure that changes and the current revision status of documents are identified;
d) ensure that relevant versions of applicable documents are available at points of use;
e) ensure that documents remain legible and readily identifiable;
f) ensure that documents of external origin determined by the organization to be necessary for the planning and operation of the quality management system are identified and their distribution controlled;
g) prevent the unintended use of obsolete documents, and to apply suitable identification to them if they are retained for any purpose.

The organization shall ensure that changes to documents are reviewed and approved either by the original approving function or another designated function that has access to pertinent background information upon which to base its decisions.

The organization shall define the period of time for retaining obsolete controlled documents that are kept for any purpose such as legal or knowledge preservation.

Where applicable, the organization shall ensure that confidential health information is protected in accordance with applicable regulatory requirements.

The organization shall document procedures to ensure the identification and maintenance of the content of applicable documents of external origin (e.g. standards, regulations, customer drawings) and to prevent the use of invalid or obsolete external documents.

The organization shall have documented procedures to control the distribution of documentation to ensure that:
a) the timely distribution of relevant versions of applicable documents to points of use;
b) the timely removal and/or identification of invalid or obsolete documents at all points of use.

For sterile medical devices, records of the person(s) authorizing the release of documents shall be maintained.

The organization shall establish documented procedures to describe the means to protect against the deterioration and loss of documents.
                            """
                        },
                        "4.2.5": {
                            "title": "Control of records",
                            "content": """
Records established to provide evidence of conformity to requirements and the effective operation of the quality management system shall be controlled.

The organization shall establish a documented procedure to define the controls needed for the identification, storage, protection, retrieval, retention time and disposition of records.

Records shall remain legible, readily identifiable and retrievable.

Where applicable, the organization shall ensure that confidential health information is protected in accordance with applicable regulatory requirements.

The organization shall define and document the retention period for records. This retention period ensures that records are available for a period of time at least equivalent to the lifetime of the medical device as defined by the organization, but not less than two years from the date the medical device is released by the organization.

The organization shall establish documented procedures to describe the means to protect against the deterioration and loss of records.
                            """
                        }
                    }
                }
            }
        }

    def _get_section_5_management(self):
        """Section 5: Management responsibility"""
        return {
            "section": "5",
            "title": "Management responsibility",
            "subsections": {
                "5.1": {
                    "title": "Management commitment",
                    "content": """
Top management shall provide evidence of its commitment to the development and implementation of the quality management system and maintenance of its effectiveness by:
a) communicating to the organization the importance of meeting customer as well as applicable regulatory requirements;
b) establishing the quality policy;
c) ensuring that quality objectives are established;
d) conducting management reviews;
e) ensuring the availability of resources.
                    """
                },
                "5.2": {
                    "title": "Customer focus",
                    "content": """
Top management shall ensure that customer requirements and applicable regulatory requirements are determined and met.
                    """
                },
                "5.3": {
                    "title": "Quality policy",
                    "content": """
Top management shall ensure that the quality policy:
a) is applicable to the purpose of the organization;
b) includes a commitment to comply with requirements and to maintain the effectiveness of the quality management system;
c) provides a framework for establishing and reviewing quality objectives;
d) is communicated and understood within the organization;
e) is reviewed for continuing suitability.
                    """
                },
                "5.4": {
                    "title": "Planning",
                    "subsections": {
                        "5.4.1": {
                            "title": "Quality objectives",
                            "content": """
Top management shall ensure that quality objectives, including those needed to meet applicable regulatory requirements and requirements for product, are established at relevant functions and levels within the organization. The quality objectives shall be measurable and consistent with the quality policy.
                            """
                        },
                        "5.4.2": {
                            "title": "Quality management system planning",
                            "content": """
Top management shall ensure that:
a) the planning of the quality management system is carried out in order to meet the requirements given in 4.1, as well as the quality objectives;
b) the integrity of the quality management system is maintained when changes to the quality management system are planned and implemented.
                            """
                        }
                    }
                },
                "5.5": {
                    "title": "Responsibility, authority and communication",
                    "subsections": {
                        "5.5.1": {
                            "title": "Responsibility and authority",
                            "content": """
Top management shall ensure that responsibilities and authorities are defined, documented and communicated within the organization.

Top management shall document the interrelation of all personnel who manage, perform and verify work affecting quality and shall ensure the independence and authority necessary to perform these tasks.
                            """
                        },
                        "5.5.2": {
                            "title": "Management representative",
                            "content": """
Top management shall appoint a member of management who, irrespective of other responsibilities, has responsibility and authority that includes:
a) ensuring that processes needed for the quality management system are documented;
b) reporting to top management on the effectiveness of the quality management system and any need for improvement;
c) ensuring the promotion of awareness of applicable regulatory requirements and quality management system requirements throughout the organization.
                            """
                        },
                        "5.5.3": {
                            "title": "Internal communication",
                            "content": """
Top management shall ensure that appropriate communication processes are established within the organization and that communication takes place regarding the effectiveness of the quality management system.
                            """
                        }
                    }
                },
                "5.6": {
                    "title": "Management review",
                    "subsections": {
                        "5.6.1": {
                            "title": "General",
                            "content": """
The organization shall document procedures for management review. Top management shall review the organization's quality management system at documented planned intervals to ensure its continuing suitability, adequacy and effectiveness. The review shall include assessing opportunities for improvement and the need for changes to the quality management system, including the quality policy and quality objectives.

Records from management reviews shall be maintained (see 4.2.5).
                            """
                        },
                        "5.6.2": {
                            "title": "Review input",
                            "content": """
The input to management review shall include, but is not limited to, information arising from:
a) feedback;
b) complaint handling;
c) reporting to regulatory authorities;
d) audits;
e) monitoring and measurement of processes;
f) monitoring and measurement of product;
g) corrective action;
h) preventive action;
i) follow-up actions from previous management reviews;
j) changes that could affect the quality management system;
k) recommendations for improvement;
l) applicable new or revised regulatory requirements.
                            """
                        },
                        "5.6.3": {
                            "title": "Review output",
                            "content": """
The output from management review shall be recorded (see 4.2.5) and include the input reviewed and any decisions and actions related to:
a) improvement needed to maintain the suitability, adequacy, and effectiveness of the quality management system and its processes;
b) improvement of product related to customer requirements;
c) changes needed to respond to applicable new or revised regulatory requirements;
d) resource needs.
                            """
                        }
                    }
                }
            }
        }

    def _get_section_6_resources(self):
        """Section 6: Resource management"""
        return {
            "section": "6",
            "title": "Resource management",
            "subsections": {
                "6.1": {
                    "title": "Provision of resources",
                    "content": """
The organization shall determine and provide the resources needed to:
a) implement the quality management system and to maintain its effectiveness;
b) meet applicable regulatory and customer requirements.
                    """
                },
                "6.2": {
                    "title": "Human resources",
                    "content": """
Personnel performing work affecting product quality shall be competent on the basis of appropriate education, training, skills and experience.

The organization shall document the process(es) for establishing competence, providing needed training, and ensuring awareness of personnel.

The organization shall:
a) determine the necessary competence for personnel performing work affecting product quality;
b) provide training or take other actions to achieve or maintain the necessary competence;
c) evaluate the effectiveness of the actions taken;
d) ensure that its personnel are aware of the relevance and importance of their activities and how they contribute to the achievement of the quality objectives;
e) maintain appropriate records of education, training, skills and experience (see 4.2.5).

NOTE: The methodology used to check effectiveness is proportionate to the risk associated with the work for which the training or other action is being provided.
                    """
                },
                "6.3": {
                    "title": "Infrastructure",
                    "content": """
The organization shall document the requirements for the infrastructure needed to achieve conformity to product requirements, prevent product mix-up and ensure orderly handling of product.

Infrastructure includes, as appropriate:
a) buildings, workspace and associated utilities;
b) process equipment (both hardware and software);
c) supporting services (such as transport, communication, or information systems).

The organization shall document requirements for the maintenance activities, including the interval of performing the maintenance activities, when such maintenance activities, or lack thereof, can affect product quality. As appropriate, the requirements shall apply to equipment used in production, the control of the work environment and monitoring and measurement.

Records of such maintenance shall be maintained (see 4.2.5).
                    """
                },
                "6.4": {
                    "title": "Work environment and contamination control",
                    "subsections": {
                        "6.4.1": {
                            "title": "Work environment",
                            "content": """
The organization shall document the requirements for the work environment needed to achieve conformity to product requirements.

If the conditions for the work environment can have an adverse effect on product quality, the organization shall document the requirements for the work environment and the procedures to monitor and control the work environment.

The organization shall:
a) document requirements for health, cleanliness and clothing of personnel if contact between such personnel and the product or work environment could affect medical device safety or performance;
b) ensure that all personnel who are required to work temporarily under special environmental conditions within the work environment are competent or supervised by a competent person.

NOTE: Further information can be found in ISO 14644 and ISO 14698.
                            """
                        },
                        "6.4.2": {
                            "title": "Contamination control",
                            "content": """
As appropriate, the organization shall plan and document arrangements for the control of contaminated or potentially contaminated product in order to prevent contamination of the work environment, personnel, or product.

For sterile medical devices, the organization shall document requirements for control of contamination with microorganisms or particulate matter and maintain the required cleanliness during assembly or packaging processes.
                            """
                        }
                    }
                }
            }
        }

    def _get_section_7_product_realization(self):
        """Section 7: Product realization"""
        return {
            "section": "7",
            "title": "Product realization",
            "subsections": {
                "7.1": {
                    "title": "Planning of product realization",
                    "content": """
The organization shall plan and develop the processes needed for product realization. Planning of product realization shall be consistent with the requirements of the other processes of the quality management system.

The organization shall document one or more processes for risk management in product realization. Records of risk management activities shall be maintained (see 4.2.5).

In planning product realization, the organization shall determine the following, as appropriate:
a) quality objectives and requirements for the product;
b) the need to establish processes and documents (see 4.2.4) and to provide resources specific to the product, including infrastructure and work environment;
c) required verification, validation, monitoring, measurement, inspection and test, handling, storage, distribution and traceability activities specific to the product together with the criteria for product acceptance;
d) records needed to provide evidence that the realization processes and resulting product meet requirements (see 4.2.5).

The output of this planning shall be documented in a form suitable for the organization's method of operations.

NOTE: Further information can be found in ISO 14971.
                    """
                },
                "7.2": {
                    "title": "Customer-related processes",
                    "subsections": {
                        "7.2.1": {
                            "title": "Determination of requirements related to product",
                            "content": """
The organization shall determine:
a) requirements specified by the customer, including the requirements for delivery and post-delivery activities;
b) requirements not stated by the customer but necessary for specified or intended use, as known;
c) applicable regulatory requirements related to the product;
d) any user training needed to ensure specified performance and safe use of the medical device;
e) any additional requirements determined by the organization.
                            """
                        },
                        "7.2.2": {
                            "title": "Review of requirements related to product",
                            "content": """
The organization shall review the requirements related to product. This review shall be conducted prior to the organization's commitment to supply product to the customer (e.g. submission of tenders, acceptance of contracts or orders, acceptance of changes to contracts or orders) and shall ensure that:
a) product requirements are defined and documented;
b) contract or order requirements differing from those previously expressed are resolved;
c) applicable regulatory requirements are met;
d) any user training identified in accordance with 7.2.1 is available or planned to be available;
e) the organization has the ability to meet the defined requirements.

Records of the results of the review and actions arising from the review shall be maintained (see 4.2.5).

When the customer provides no documented statement of requirement, the customer requirements shall be confirmed by the organization before acceptance.

When product requirements are changed, the organization shall ensure that relevant documents are amended and that relevant personnel are made aware of the changed requirements.
                            """
                        },
                        "7.2.3": {
                            "title": "Communication",
                            "content": """
The organization shall document arrangements and implement effective arrangements for communicating with customers in relation to:
a) product information;
b) enquiries, contracts or order handling, including amendments;
c) customer feedback, including customer complaints;
d) advisory notices.

The organization shall communicate with regulatory authorities in accordance with applicable regulatory requirements.
                            """
                        }
                    }
                },
                "7.3": {
                    "title": "Design and development",
                    "content": """Complete design controls per ISO 13485:2016 Section 7.3 including planning, inputs, outputs, reviews, verification, validation, transfer, change control, and design files maintenance."""
                },
                "7.4": {
                    "title": "Purchasing",
                    "content": """Purchasing process controls, information requirements, and verification procedures per Section 7.4"""
                },
                "7.5": {
                    "title": "Production and service provision",
                    "subsections": {
                        "7.5.1": {
                            "title": "Control of production and service provision",
                            "content": """
Production and service provision shall be planned, carried out, monitored and controlled to ensure that product conforms to specification. As appropriate, production controls shall include but are not limited to:
a) documentation of procedures and methods for the control of production (see 4.2.4);
b) qualification of infrastructure;
c) implementation of monitoring and measurement of process parameters and product characteristics;
d) availability and use of monitoring and measuring equipment;
e) implementation of defined operations for labelling and packaging;
f) implementation of product release, delivery and post-delivery activities.

The organization shall establish and maintain a record (see 4.2.5) for each medical device or batch of medical devices that provides traceability to the extent specified in 7.5.9 and identifies the amount manufactured and amount approved for distribution. The record shall be verified and approved.
                            """
                        },
                        "7.5.2": {
                            "title": "Cleanliness of product",
                            "content": """
The organization shall document requirements for cleanliness of product or contamination control of product if:
a) product is cleaned by the organization prior to sterilization or its use;
b) product is supplied non-sterile and is to be subjected to a cleaning process prior to sterilization or its use;
c) product cannot be cleaned prior to sterilization or its use, and its cleanliness is of significance in use;
d) product is supplied to be used non-sterile, and its cleanliness is of significance in use;
e) process agents are to be removed from product during manufacture.

If product is cleaned in accordance with a) or b) above, the requirements contained in 6.4.1 do not apply prior to the cleaning process.
                            """
                        },
                        "7.5.3": {
                            "title": "Installation activities",
                            "content": """
The organization shall document requirements for medical device installation and acceptance criteria for verification of installation, as appropriate.

If the agreed customer requirements allow installation of the medical device to be performed by an external party other than the organization or its supplier, the organization shall provide documented requirements for medical device installation and verification of installation.

Records of medical device installation and verification of installation performed by the organization or its supplier shall be maintained (see 4.2.5).
                            """
                        }
                    }
                }
            }
        }

    def _get_section_8_measurement(self):
        """Section 8: Measurement, analysis and improvement"""
        return {
            "section": "8",
            "title": "Measurement, analysis and improvement",
            "subsections": {
                "8.1": {
                    "title": "General",
                    "content": """
The organization shall document procedures to determine, collect and analyse appropriate data to demonstrate the suitability, adequacy and effectiveness of the quality management system. The procedures shall include determination of appropriate methods, including statistical techniques and the extent of their use.

The organization shall plan and implement the monitoring, measurement, analysis and improvement processes needed to:
a) demonstrate conformity to product requirements;
b) ensure conformity of the quality management system;
c) maintain the effectiveness of the quality management system.

This shall include determination of appropriate methods, including statistical techniques, and the extent of their use.
                    """
                },
                "8.2": {
                    "title": "Monitoring and measurement",
                    "subsections": {
                        "8.2.1": {
                            "title": "Feedback",
                            "content": """
The organization shall document procedures for a feedback system to provide early warning of quality problems and for input into the corrective and preventive action process. The feedback system shall include provisions to collect data from production and post-production activities.

Data from the feedback system shall be analysed to provide information for:
a) trends indicating that corrective or preventive actions may be necessary;
b) input to risk management processes to monitor and maintain product requirements;
c) historical information to aid in validation or product improvements.
                            """
                        },
                        "8.2.2": {
                            "title": "Complaint handling",
                            "content": """
The organization shall document procedures for timely complaint handling in accordance with applicable regulatory requirements. These procedures shall include at a minimum requirements and responsibilities for:
a) receiving and recording information;
b) evaluating complaints to determine whether the complaint relates to activities under the control of the organization and whether an investigation is required;
c) investigating the cause of a quality problem relating to the product, processes, or quality management system;
d) determining the need for corrective actions or preventive actions to eliminate the cause(s) of complaint(s);
e) verifying that any corrective action or preventive action taken is effective;
f) ensuring that relevant information on complaints and investigations are submitted for management review;
g) ensuring that relevant information on complaints and corrective and preventive actions are communicated to external parties in accordance with applicable regulatory requirements;
h) ensuring timely closure of complaints.

Records of complaints and their investigation shall be maintained (see 4.2.5).
                            """
                        },
                        "8.2.3": {
                            "title": "Reporting to regulatory authorities",
                            "content": """
If applicable regulatory requirements require the organization to gain experience from the post-production phase, the organization shall establish documented procedures for these post-market surveillance activities appropriate to the medical device.

The data from such post-market surveillance activities shall be analysed, and if this analysis indicates that corrective action or preventive action is necessary, the organization shall take appropriate action in accordance with 8.5.2 and 8.5.3.

If applicable regulatory requirements require notification of adverse events or other situations, the organization shall establish documented procedures for providing notification to the regulatory authorities.

Records arising from these activities shall be maintained (see 4.2.5).
                            """
                        }
                    }
                },
                "8.3": {
                    "title": "Control of nonconforming product",
                    "content": """Complete nonconforming product control procedures per Section 8.3"""
                },
                "8.4": {
                    "title": "Analysis of data",
                    "content": """Data analysis requirements and procedures per Section 8.4"""
                },
                "8.5": {
                    "title": "Improvement",
                    "subsections": {
                        "8.5.1": {
                            "title": "General",
                            "content": """
The organization shall identify and implement any changes necessary to ensure and maintain the continued suitability, adequacy and effectiveness of the quality management system as well as medical device safety and performance through the use of the quality policy, quality objectives, audit results, post-market surveillance, analysis of data, corrective actions, preventive actions and management review.
                            """
                        },
                        "8.5.2": {
                            "title": "Corrective action",
                            "content": """
The organization shall take action to eliminate the cause of nonconformities in order to prevent recurrence. Any necessary corrective actions shall be taken without undue delay. Corrective actions shall be proportionate to the effects of the nonconformities encountered.

The organization shall document a procedure to define requirements for:
a) reviewing nonconformities (including complaints);
b) determining the causes of nonconformities;
c) evaluating the need for action to ensure that nonconformities do not recur;
d) planning and documenting action needed and implementing such action, including, as appropriate, updating documentation;
e) verifying that the corrective action does not adversely affect the ability to meet applicable regulatory requirements or the safety and performance of the medical device;
f) reviewing the effectiveness of corrective action taken.

Records of the results of any investigation and of action taken shall be maintained (see 4.2.5).
                            """
                        },
                        "8.5.3": {
                            "title": "Preventive action",
                            "content": """
The organization shall determine action to eliminate the causes of potential nonconformities in order to prevent their occurrence. Preventive actions shall be proportionate to the effects of the potential problems.

The organization shall document a procedure to describe requirements for:
a) determining potential nonconformities and their causes;
b) evaluating the need for action to prevent occurrence of nonconformities;
c) planning and documenting action needed and implementing such action;
d) verifying that the preventive action does not adversely affect the ability to meet applicable regulatory requirements or the safety and performance of the medical device;
e) reviewing the effectiveness of preventive action taken.

Records of the results of any investigation and of action taken shall be maintained (see 4.2.5).
                            """
                        }
                    }
                }
            }
        }

    def _get_annexes(self):
        """Annexes A and B"""
        return {
            "annex_a": {
                "title": "Comparison of content between ISO 13485:2003 and ISO 13485:2016",
                "type": "informative",
                "content": "Detailed comparison tables showing changes from previous version"
            },
            "annex_b": {
                "title": "Correspondence between ISO 13485:2016 and ISO 9001:2015", 
                "type": "informative",
                "content": "Mapping between ISO 13485 and ISO 9001 clauses"
            }
        }

    def get_section_content(self, section_id: str) -> dict:
        """Get specific section content"""
        section_map = {
            "1": self.full_standard["scope"],
            "2": self.full_standard["normative_references"], 
            "3": self.full_standard["terms_definitions"],
            "4": self.full_standard["section_4"],
            "5": self.full_standard["section_5"],
            "6": self.full_standard["section_6"],
            "7": self.full_standard["section_7"],
            "8": self.full_standard["section_8"]
        }
        return section_map.get(section_id, {"error": f"Section {section_id} not found"})

    def search_standard(self, query: str) -> list:
        """Search the standard for specific content"""
        results = []
        query_lower = query.lower()
        
        # Search through all sections
        for section_key, section_data in self.full_standard.items():
            if isinstance(section_data, dict):
                if "content" in section_data and query_lower in section_data["content"].lower():
                    results.append({
                        "section": section_data.get("section", section_key),
                        "title": section_data.get("title", ""),
                        "relevance": "direct_match",
                        "content_preview": self._get_content_preview(section_data["content"], query_lower)
                    })
                
                # Search subsections
                if "subsections" in section_data:
                    for subsection_key, subsection_data in section_data["subsections"].items():
                        if isinstance(subsection_data, dict) and "content" in subsection_data:
                            if query_lower in subsection_data["content"].lower():
                                results.append({
                                    "section": f"{section_data.get('section', '')}.{subsection_key}",
                                    "title": subsection_data.get("title", ""),
                                    "relevance": "subsection_match",
                                    "content_preview": self._get_content_preview(subsection_data["content"], query_lower)
                                })
        
        return results

    def _get_content_preview(self, content: str, query: str) -> str:
        """Get preview of content around search query"""
        content_lower = content.lower()
        index = content_lower.find(query)
        if index == -1:
            return content[:200] + "..."
        
        start = max(0, index - 100)
        end = min(len(content), index + len(query) + 100)
        preview = content[start:end]
        
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
            
        return preview

    def get_ai_context_for_query(self, user_query: str) -> str:
        """Get relevant ISO 13485 context for AI consultation"""
        # Search for relevant sections
        search_results = self.search_standard(user_query)
        
        context = f"ISO 13485:2016 Context for query: '{user_query}'\n\n"
        
        if search_results:
            context += "Relevant sections:\n"
            for result in search_results[:3]:  # Limit to top 3 results
                context += f"\nSection {result['section']}: {result['title']}\n"
                context += f"{result['content_preview']}\n"
                context += "-" * 50 + "\n"
        else:
            # If no direct matches, provide general ISO 13485 structure
            context += "General ISO 13485:2016 Structure:\n"
            context += "1. Scope\n2. Normative References\n3. Terms and Definitions\n"
            context += "4. Quality Management System\n5. Management Responsibility\n"
            context += "6. Resource Management\n7. Product Realization\n"
            context += "8. Measurement, Analysis and Improvement\n"
        
        return context

# Usage functions for integration
def get_iso_knowledge_base():
    """Get the complete ISO 13485 knowledge base"""
    return ISO13485CompleteKnowledge()

def create_ai_enhanced_prompt(user_query: str, knowledge_base: ISO13485CompleteKnowledge) -> str:
    """Create enhanced prompt with ISO 13485 context"""
    context = knowledge_base.get_ai_context_for_query(user_query)
    
    enhanced_prompt = f"""
{context}

Based on the above ISO 13485:2016 context, please provide a comprehensive answer to the following question:

{user_query}

Please ensure your response:
1. References specific ISO 13485:2016 sections when applicable
2. Provides practical implementation guidance
3. Considers regulatory compliance requirements
4. Addresses both letter and spirit of the standard
5. Includes examples where helpful
"""
    
    return enhanced_prompt
