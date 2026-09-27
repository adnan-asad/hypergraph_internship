# Six manual spot checks

Six qualitative developer checks have now been recorded; only C004 has an explicit numeric rating. See human_spotchecks.csv and human_feedback_source.json. Read the supplied examples; enter your judgment in human_spotchecks.csv. Coherence: 1=incoherent, 2=mixed, 3=mostly coherent, 4=clear specific theme. Faithfulness: accurate_informative / supported_but_vague / unsupported_or_wrong / insufficient_evidence. A quoted example is not a claim about every member. You may disagree with the LLM; explain why.

## C004

Group size: 1322.

- (component) Iterative training loop workflow
- (technique) Confidence‑interval based neighbor selection
- (component) Cutoff function
- (technique) Automatic batch size determination
- (technique) Unit cell displacement enumeration
- (component) STM‑image database and analysis pipeline
- (metric) discovery rate
- (task) generation of input files for cluster expansion
- (problem) multi-species system modeling
- (component) Web applications
- (technique) Ensemble-averaged feature importance
- (metric) Score [a.u.]
- (technique) Sub‑meV regression target
- (method) Hillert model
- (future_topic) Accelerating meso‑level material design through AI‑driven defect‑property translation

LLM judgment: **1**. STM-image pipelines, batch-size determination, cluster-expansion input generation, web applications, and the Hillert model do not establish one specific concept. Generic scores and cutoff functions add no demonstrated link among these topics.

Developer feedback: The group is too large for me to agree or disagree confidently; I give it 1. This rating reflects uncertainty about group size/coverage, not an exhaustive assessment of all members.

## C006

Group size: 284.

- (author) Shyue Ping Ong
- (author) Ye Ding
- (author) Karin Rabe
- (author) Yu-Chuan Hsu
- (author) Pinar Acar
- (author) Lixin Sun
- (author) Thanh Nguyen
- (author) Houlong Zhuang
- (author) James Kermode
- (author) Yu Xia
- (cited_work) SE(3)-Equivariant Graph Neural Networks
- (cited_work) GAP
- (author) Andrea Centrone
- (author) Hai-Chen Wang
- (author) David Skinner

LLM judgment: **1**. The sample is predominantly author names, including Shyue Ping Ong, Karin Rabe, and Andrea Centrone. SE(3)-Equivariant Graph Neural Networks and GAP are the only explicit scientific-method topics and cannot establish a concept for the names alone.

Developer feedback: The examples have author names and only some connection. No explicit numerical rating or agreement decision was supplied.

## F002

Group size: 1234.

Label: energy / potential / dft / force

Gloss: Extractive summary only: 1234 nodes; examples include AMBER force field; Universal Force Field; Force‑field benchmarking

- (method) AMBER force field
- (method) Universal Force Field
- (task) Force‑field benchmarking
- (task) Classical force‑field property benchmarking
- (problem) Accuracy limitations of classical force fields
- (task) Prediction of Energies, Forces and Torques for Multi‑Component Materials
- (task) Electronic band‑structure prediction
- (metric) energy RMSE (meV)
- (component) BANDS
- (component) CGCNN model for deformation potential
- (task) Liquid silicon structural analysis
- (claim) By decoupling body‑order from the number of message‑passing iterations, MACE has a small receptive field of approximately 4–5 Å per layer, enabling efficient parallelisation across GPUs.
- (claim) The model can fit 2.8 × 10⁹ non‑zero complex‑valued Hamiltonian matrix elements with only ~10⁵ real trainable parameters, indicating high capacity efficiency.
- (claim) Beyond‑DFT methods (HSE06, PBE0, G0W0, DMFT) are generated for a subset of materials to provide higher‑level reference data and enable uncertainty quantification.
- (component) NVT thermostat during training
- (technique) Alpha2F spectral function calculation
- (task) Energy gap (∆ε) prediction
- (technique) Energy‑gradient force derivation
- (task) Prediction of potential energy, atomic forces, and virial tensor
- (task) DFT energy and force prediction

Relation context:
[
  {
    "relation": "extends",
    "year": 2022,
    "members": [
      "graph neural networks with three-body interactions",
      "graph neural network",
      "Message Passing Neural Network",
      "DimeNet",
      "Tersoff bond order potential",
      "embedded-atom-method",
      "Modified Embedded Atom Method",
      "Behler‑Parrinello Neural Network Potential"
    ],
    "endpoints_truncated": true
  },
  {
    "relation": "addresses",
    "year": 2020,
    "members": [
      "JARVIS integrated materials design infrastructure",
      "Materials property calculation",
      "Solar‑cell efficiency screening",
      "Thermoelectric performance prediction",
      "STM image analysis",
      "Force‑field benchmarking",
      "Heterostructure design",
      "Electronic structure calculation"
    ],
    "endpoints_truncated": true
  },
  {
    "relation": "addresses",
    "year": 2024,
    "members": [
      "EquiformerV2",
      "atomic energy prediction",
      "atomic force prediction",
      "adsorption energy calculation",
      "molecular property prediction on QM9",
      "relaxation on OC20 dataset",
      "Energy prediction",
      "Force prediction"
    ],
    "endpoints_truncated": true
  }
]

LLM judgment: **accurate_informative**. Energy, potential, DFT and force form an identifiable calculation/prediction subject supported by explicit energy-force tasks. Named force fields and their benchmarking provide useful concrete examples, and the relations independently connect models to these prediction tasks.

Developer feedback: The group is very large, but the examples appear related to energy potentials and DFT transforms. No explicit categorical rating was supplied.

## F003

Group size: 31.

Label: dft / high / throughput / calculations

Gloss: Extractive summary only: 31 nodes; examples include high-throughput DFT validation; High‑throughput DFT; Scalable high‑throughput DFT management

- (technique) high-throughput DFT validation
- (technique) High‑throughput DFT
- (problem) Scalable high‑throughput DFT management
- (problem) Computational cost of large‑scale DFT
- (problem) Computational cost in high-throughput DFT
- (claim) The workflow software FireWorks together with the custodian job‑management tool automatically manages high‑throughput DFT calculations, self‑heals failed runs, and applies material‑type‑specific workflows.
- (dataset) DFT carbon reference data
- (problem) Benchmarking beyond‑DFT methods
- (component) JARVIS-Beyond-DFT database
- (task) High-throughput DFT calculations
- (component) HT‑DFT+U workflow
- (claim) AFLOW implements DFT+U using the Dudarev formalism with default Ueff values for a wide range of elements.
- (problem) DFT‑level accuracy with linear scaling
- (cited_work) Dudarev DFT+U
- (method) DFT+U
- (technique) High‑throughput DFT calculations

LLM judgment: **accurate_informative**. The label reconstructs the specific subject of high-throughput DFT calculations. Validation, management and computational-cost members, together with the FireWorks/custodian claim, substantiate that subject; the gloss supplies relevant task examples.

Developer feedback: High-throughput and DFT keywords occur, but I cannot say for sure that they are semantically connected or form a scientifically coherent meaning. No explicit categorical rating was supplied.

## F001

Group size: 954.

Label: training / regression / matbench / sampling

Gloss: Extractive summary only: 954 nodes; examples include Semi‑Grand Canonical Monte Carlo with umbrella sampling; Semi-Grand Canonical Monte Carlo; Metropolis Monte Carlo

- (technique) Semi‑Grand Canonical Monte Carlo with umbrella sampling
- (method) Semi-Grand Canonical Monte Carlo
- (method) Metropolis Monte Carlo
- (cited_work) Monte Carlo
- (cited_work) kinetic Monte Carlo
- (technique) Batch size adjustment
- (problem) Combinatorial blow-up in candidate generation
- (problem) Memory usage limitations in heterogeneous datasets
- (component) Tree ensemble model
- (component) Mode‑I and Mode‑II training pipelines
- (cited_work) Matminer
- (claim) Accurate regression models can still produce high false‑positive rates near the 0 eV/atom convex‑hull decision boundary.
- (technique) Set2Set pooling
- (component) SLME screening module
- (technique) Error function screening
- (technique) Ensemble-averaged feature importance
- (component) RELAX1
- (claim) Starting the training loop with sufficient data sampling a relevant portion of phase space is important for obtaining generalizable models.
- (technique) Conditional flow matching regression
- (task) Matbench regression tasks

Relation context:
[
  {
    "relation": "cites",
    "year": 2023,
    "members": [
      "Bridging scales with Machine Learning: From first principles statistical mechanics to continuum phase field computations to study order-disorder transitions in LixCoO2",
      "Billiard Walk",
      "Cahn-Hilliard equation",
      "Allen-Cahn equation",
      "Monte Carlo",
      "kinetic Monte Carlo",
      "deal.II library",
      "mechanoChemFEM code"
    ],
    "endpoints_truncated": true
  }
]

LLM judgment: **supported_but_vague**. Training, regression, Matbench and sampling each have witnesses, and the Monte Carlo examples are present. However, the label and three sampling examples do not explain how these diverse activities form a scientific subject or characterize the training and screening material.

Developer feedback: Vague, but searching methods appear together. No explicit support/overclaim category was supplied.

## F005

Group size: 178.

Label: training / active / gradient / rate

Gloss: Extractive summary only: 178 nodes; examples include Hessian eigenvalue spectrum loss; Hessian eigenvalue spectrum loss; Extension of Hessian‑based training to other higher‑order physical observables

- (component) Hessian eigenvalue spectrum loss
- (technique) Hessian eigenvalue spectrum loss
- (future_topic) Extension of Hessian‑based training to other higher‑order physical observables
- (component) Hessian‑based training augmentation
- (technique) Hessian‑based loss augmentation
- (technique) Active learning
- (method) Light Gradient-Boosting Machine
- (technique) Training set augmentation via intermediate MD
- (component) Active learning workflow with Billiard Walk sampling
- (cited_work) Denoising Pre-training
- (technique) Analytic Gradient Evaluation
- (technique) Unsupervised classification
- (technique) Angular-modified attention weights
- (technique) concurrent learning procedure
- (technique) Noisy Nodes data augmentation
- (technique) Transfer learning of elemental embeddings
- (technique) Large-scale pretraining
- (technique) Active‑learning‑guided data acquisition
- (technique) conjugate-gradient relaxation
- (technique) Exponential learning rate decay

Relation context:
[
  {
    "relation": "uses_component",
    "year": 2024,
    "members": [
      "Phonax (E(3)-equivariant graph neural network framework for phonon and Hessian prediction)",
      "Phonax framework",
      "Extended periodic graph construction",
      "Hessian‑based training augmentation",
      "Symmetry‑aware E(3)‑equivariant GNN energy model",
      "Irreducible‑representation analysis for IR/Raman activity",
      "Hessian eigenvalue spectrum loss",
      "Generalized energy model with electric‑field coupling"
    ],
    "endpoints_truncated": true
  },
  {
    "relation": "uses_technique",
    "year": 2024,
    "members": [
      "Phonax (E(3)-equivariant graph neural network framework for phonon and Hessian prediction)",
      "Automatic differentiation of second derivatives",
      "Hessian‑based loss augmentation",
      "Acoustic sum‑rule enforcement via equivariance",
      "Fine‑tuning with experimental vibrational spectra",
      "Hessian eigenvalue spectrum loss",
      "Auto‑differentiation of energy model",
      "Perturbative expansion in external electric field"
    ],
    "endpoints_truncated": true
  },
  {
    "relation": "uses_technique",
    "year": 2019,
    "members": [
      "DeePMD training protocol for diffusion coefficient computation",
      "Active learning",
      "Nosé-Hoover thermostat",
      "Interquartile range outlier filtering",
      "Minimum ion-ion distance cutoff",
      "Maximum bond variation check",
      "Batch size adjustment",
      "Self-consistent training"
    ],
    "endpoints_truncated": true
  },
  {
    "relation": "uses_technique",
    "year": 2023,
    "members": [
      "DeePMD-kit v2",
      "Local coordinate frame construction",
      "Neighbor padding",
      "Tensorial property fitting",
      "GPU-accelerated custom operators",
      "Distance-based neighbor sorting",
      "Smooth switching function",
      "Self-attention mechanism"
    ],
    "endpoints_truncated": true
  }
]

LLM judgment: **supported_but_vague**. The Hessian-loss examples are faithfully extracted and training, active learning, gradients and learning rates have witnesses. Nevertheless, the keyword label does not convey the phonon/Hessian training subject evidenced by the gloss and Phonax relations, or explain its connection to the other training techniques.

Developer feedback: Same assessment as F001: vague, with searching methods together. No explicit support/overclaim category was supplied.
