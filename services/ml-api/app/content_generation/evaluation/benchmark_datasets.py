"""Benchmark curriculum datasets (PDF & PPTX) and gold-standard reference questions.

Represents authentic, curriculum-aligned materials for 5to año de secundaria (16-17 años)
across multiple subject areas (Física, Química, Biología, Historia, Filosofía, Ecología, Geografía)
with varied document lengths (3-5 pages or slides), diverse information densities, and gold-standard
teacher-reviewed questions for provenance and pedagogical quality baselines.
"""

import hashlib
from dataclasses import dataclass, field

from app.content_generation.schemas.extracted_document import (
    DocumentType,
    DocumentUnitType,
    ExtractedDocument,
    ExtractedUnit,
)
from app.content_generation.schemas.generated_questions import (
    BloomTaxonomy,
    GeneratedQuestionDraft,
    QuestionOptionDraft,
    QuestionSourceReference,
    QuestionType,
)


@dataclass
class BenchmarkItem:
    """A benchmark curriculum document bundle with teacher reference questions."""

    name: str
    document: ExtractedDocument
    reference_questions: list[GeneratedQuestionDraft] = field(default_factory=list)
    id: str = ""
    subject: str = "Ciencias"
    topic: str = ""
    format: str = "pdf"
    total_units: int = 1
    complexity_level: str = "intermedio"
    version: str = "1.0"
    checksum: str = ""

    def __post_init__(self) -> None:
        if not self.checksum and self.document and self.document.units:
            concat_text = "".join(u.text for u in self.document.units)
            self.checksum = hashlib.sha256(concat_text.encode("utf-8")).hexdigest()[:16]
        if not self.total_units and self.document:
            self.total_units = len(self.document.units)
        if not self.format and self.document:
            self.format = self.document.document_type.value


# ==============================================================================
# 1. FÍSICA: Termodinámica (PDF, 3 páginas, intermedia)
# ==============================================================================
def get_thermodynamics_pdf_benchmark() -> BenchmarkItem:
    """PDF Benchmark: 3-page science curriculum on thermodynamics."""
    unit1_text = (
        "La Primera Ley de la Termodinámica establece el principio de conservación de la energía: "
        "la energía total de un sistema aislado permanece constante, no se crea ni se destruye, solo se transforma. "
        "En procesos biológicos celulares, la energía química contenida en los enlaces de glucosa se transforma en ATP "
        "y energía térmica. La variación de energía interna delta U equivale al calor absorbido Q menos el trabajo W realizado."
    )
    unit2_text = (
        "La Segunda Ley de la Termodinámica introduce la noción de entropía S como medida del desorden molecular o dispersión "
        "de energía. En todo proceso espontáneo, la entropía total del universo tiende a aumentar de manera irreversible. "
        "Para mantener una baja entropía interna y alta organización celular, los seres vivos consumen energía libre de Gibbs G, "
        "disipando calor y productos de degradación hacia el entorno circundante."
    )
    unit3_text = (
        "La transferencia de calor ocurre a través de tres mecanismos físicos fundamentales: conducción, convección y radiación. "
        "La conducción térmica es la transferencia de energía cinética a través de colisiones intermoleculares en sólidos y fluidos. "
        "La convección implica el transporte macroscópico de masa en fluidos por gradientes de densidad, mientras que la radiación "
        "térmica transmite energía mediante ondas electromagnéticas infrarrojas sin requerir un medio material soporte."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PDF,
        original_filename="termodinamica_5to.pdf",
        total_units=3,
        units=[
            ExtractedUnit(type=DocumentUnitType.PAGE, index=1, text=unit1_text),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=2, text=unit2_text),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=3, text=unit3_text),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Primera Ley de la Termodinámica",
        question_text="¿Cómo se define el postulado central de la Primera Ley de la Termodinámica en relación con la energía?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.400,
        bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
        options=[
            QuestionOptionDraft(
                text="La energía total de un sistema aislado permanece constante, no se crea ni se destruye, solo se transforma.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="La energía total de un sistema aislado se disipa gradualmente hasta alcanzar el cero absoluto.",
                is_correct=False,
                misconception_explanation="Confusión común entre conservación de energía y disipación térmica.",
            ),
            QuestionOptionDraft(
                text="La energía interna se crea espontáneamente cuando la temperatura del sistema se incrementa.",
                is_correct=False,
                misconception_explanation="Violación conceptual del principio de conservación.",
            ),
            QuestionOptionDraft(
                text="El trabajo realizado por el sistema siempre destruye una fracción proporcional de calor.",
                is_correct=False,
                misconception_explanation="Interpretación errónea de la equivalencia trabajo-calor.",
            ),
        ],
        explanation="La Primera Ley establece que en un sistema aislado la energía total se conserva, transformándose entre distintas modalidades.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=1,
                snippet="la energía total de un sistema aislado permanece constante, no se crea ni se destruye, solo se transforma",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-01-fis-termo",
        name="termodinamica_pdf",
        subject="Física",
        topic="Termodinámica y Transferencia de Calor en Sistemas Físico-Biológicos",
        format="pdf",
        total_units=3,
        complexity_level="intermedio",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 2. FÍSICA: Movimiento Armónico Simple (PPTX, 4 diapositivas, avanzada)
# ==============================================================================
def get_harmonic_motion_pptx_benchmark() -> BenchmarkItem:
    """PPTX Benchmark: 4-slide curriculum on Simple Harmonic Motion."""
    slide1_text = (
        "El Movimiento Armónico Simple (MAS) es un movimiento periódico oscilatorio donde la aceleración es directamente "
        "proporcional al desplazamiento de la partícula respecto al punto de equilibrio y de sentido opuesto. "
        "La ecuación cinemática de la elongación es x(t) = A * cos(omega * t + phi), donde A es la amplitud y omega la frecuencia angular."
    )
    slide2_text = (
        "La fuerza restauradora en el oscilador masa-resorte sigue la Ley de Hooke: F = -k * x, donde k es la constante elástica. "
        "El signo negativo indica que la fuerza recuperadora siempre apunta hacia la posición de equilibrio central. "
        "El periodo de oscilación T depende exclusivamente de la masa suspendida m y de la rigidez del resorte: T = 2 * pi * sqrt(m / k)."
    )
    slide3_text = (
        "En un oscilador armónico ideal sin fricción, la energía mecánica total se conserva constante y equivale a E = (1/2) * k * A^2. "
        "En los extremos de máxima elongación (+A y -A), la velocidad es nula y toda la energía es potencial elástica. "
        "Al cruzar por el punto de equilibrio central (x = 0), la energía potencial se anula y la energía cinética alcanza su valor máximo."
    )
    slide4_text = (
        "El péndulo simple describe un MAS para pequeñas amplitudes angulares menores a 15 grados sexagesimales. "
        "El periodo del péndulo simple es T = 2 * pi * sqrt(L / g), siendo independiente de la masa de la lenteja oscilante. "
        "El fenómeno de resonancia ocurre cuando la frecuencia excitadora externa coincide con la frecuencia natural del sistema oscilante."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PPTX,
        original_filename="movimiento_armonico_simple.pptx",
        total_units=4,
        units=[
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=1, text=slide1_text),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=2, text=slide2_text),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=3, text=slide3_text),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=4, text=slide4_text),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Energía en el Oscilador Armónico",
        question_text="¿En qué posición de la trayectoria de un oscilador armónico simple la energía cinética alcanza su valor máximo?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.550,
        bloom_taxonomy=BloomTaxonomy.ANALYZE,
        options=[
            QuestionOptionDraft(
                text="Al cruzar por el punto de equilibrio central (x = 0), donde la energía potencial se anula.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="En los extremos de máxima elongación (+A y -A), donde la velocidad es máxima.",
                is_correct=False,
                misconception_explanation="En los extremos la velocidad es cero y la energía cinética es nula.",
            ),
            QuestionOptionDraft(
                text="En el punto medio entre el equilibrio y el extremo positivo.",
                is_correct=False,
                misconception_explanation="La energía cinética se reparte pero no es máxima.",
            ),
            QuestionOptionDraft(
                text="La energía cinética permanece constante en todos los puntos de la trayectoria.",
                is_correct=False,
                misconception_explanation="La energía total se conserva, pero la energía cinética fluctúa con la posición.",
            ),
        ],
        explanation="Al pasar por el punto de equilibrio central no hay elongación, por lo que toda la energía mecánica se transforma en energía cinética.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.SLIDE,
                index=3,
                snippet="Al cruzar por el punto de equilibrio central (x = 0), la energía potencial se anula y la energía cinética alcanza su valor máximo",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-02-fis-mas",
        name="mas_pptx",
        subject="Física",
        topic="Movimiento Armónico Simple y Oscilaciones Mecánicas",
        format="pptx",
        total_units=4,
        complexity_level="avanzado",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 3. QUÍMICA: Estequiometría y Leyes Ponderales (PDF, 4 páginas, intermedia)
# ==============================================================================
def get_stoichiometry_pdf_benchmark() -> BenchmarkItem:
    """PDF Benchmark: 4-page curriculum on chemical stoichiometry."""
    u1 = (
        "La Ley de Conservación de la Masa formulada por Antoine Lavoisier establece que en toda reacción química ordinaria, "
        "la masa total de los reactivos es exactamente igual a la masa total de los productos obtenidos. "
        "Los átomos no se crean ni se destruyen durante el enlace o ruptura química, únicamente se reorganizan en nuevas sustancias."
    )
    u2 = (
        "La Ley de las Proporciones Definidas o Ley de Proust determina que cuando dos o más elementos se combinan químicamente "
        "para formar un compuesto específico, lo hacen siempre en una relación de masa constante e invariable. "
        "Si los reactivos se suministran en proporciones distintas a la estequiométrica, uno de ellos sobrará al consumirse totalmente el otro."
    )
    u3 = (
        "El reactivo limitante es aquella sustancia que se consume por completo en primer lugar durante una reacción química, "
        "determinando la cantidad máxima teórica de producto que puede sintetizarse. "
        "El reactivo en exceso es aquel que permanece presente en la mezcla tras haberse agotado el reactivo limitante."
    )
    u4 = (
        "El rendimiento porcentual de una reacción cuantifica la eficiencia del proceso industrial o experimental de síntesis. "
        "Se calcula mediante la fórmula: Rendimiento (%) = (Masa real obtenida / Rendimiento teórico calculado) * 100. "
        "Factores como pérdidas por filtración, reacciones secundarias paralelas o impurezas reducen el rendimiento práctico por debajo del 100%."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PDF,
        original_filename="estequiometria_quimica.pdf",
        total_units=4,
        units=[
            ExtractedUnit(type=DocumentUnitType.PAGE, index=1, text=u1),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=2, text=u2),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=3, text=u3),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=4, text=u4),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Reactivo Limitante",
        question_text="¿Qué función cumple el reactivo limitante en el cálculo de una reacción química?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.450,
        bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
        options=[
            QuestionOptionDraft(
                text="Es la sustancia que se consume por completo primero y determina la cantidad máxima de producto sintetizable.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="Es el reactivo que sobra al final de la reacción y no reacciona con los demás componentes.",
                is_correct=False,
                misconception_explanation="Esa es la definición del reactivo en exceso.",
            ),
            QuestionOptionDraft(
                text="Es el catalizador que acelera la reacción sin alterar la masa final.",
                is_correct=False,
                misconception_explanation="Un reactivo limitante se consume en la reacción, a diferencia de un catalizador.",
            ),
            QuestionOptionDraft(
                text="Es la sustancia con menor masa molar en la ecuación química balanceada.",
                is_correct=False,
                misconception_explanation="El reactivo limitante depende de los moles y coeficientes estequiométricos, no solo de la masa molar.",
            ),
        ],
        explanation="El reactivo limitante se agota primero y limita la formación posterior de producto.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=3,
                snippet="El reactivo limitante es aquella sustancia que se consume por completo en primer lugar durante una reacción química, determinando la cantidad máxima teórica de producto que puede sintetizarse",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-03-qui-esteq",
        name="estequiometria_pdf",
        subject="Química",
        topic="Estequiometría de Reacciones y Leyes Ponderales",
        format="pdf",
        total_units=4,
        complexity_level="intermedio",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 4. QUÍMICA: Enlace Químico y Fuerzas Intermoleculares (PPTX, 3 diapositivas, básica)
# ==============================================================================
def get_chemical_bonding_pptx_benchmark() -> BenchmarkItem:
    """PPTX Benchmark: 3-slide curriculum on chemical bonding."""
    s1 = (
        "El enlace iónico se forma por la transferencia completa de uno o más electrones de valencia desde un átomo metálico "
        "electropositivo hacia un no metal electronegativo. Se generan cationes y aniones que se atraen mediante intensas fuerzas "
        "electrostáticas coulombianas, conformando redes cristalinas sólidas con elevados puntos de fusión."
    )
    s2 = (
        "El enlace covalente involucra la compartición de pares de electrones entre átomos no metálicos. "
        "En el enlace covalente apolar o puro, la diferencia de electronegatividad es nula y los electrones se comparten simétricamente. "
        "En el enlace covalente polar, el átomo más electronegativo atrae la densidad electrónica generando dipolos moleculares permanentes."
    )
    s3 = (
        "Las fuerzas intermoleculares determinan las propiedades físicas macroscópicas como el punto de ebullición y la solubilidad. "
        "Los puentes de hidrógeno son interacciones dipolo-dipolo especialmente intensas que se establecen cuando el hidrógeno está "
        "unido covalentemente a átomos pequeños y muy electronegativos como flúor, oxígeno o nitrógeno (F, O, N)."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PPTX,
        original_filename="enlace_quimico_intermolecular.pptx",
        total_units=3,
        units=[
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=1, text=s1),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=2, text=s2),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=3, text=s3),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Puentes de Hidrógeno",
        question_text="¿Cuáles son las condiciones atómicas requeridas para que se forme una interacción por puente de hidrógeno?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.380,
        bloom_taxonomy=BloomTaxonomy.REMEMBER,
        options=[
            QuestionOptionDraft(
                text="El hidrógeno debe estar unido covalentemente a átomos pequeños y muy electronegativos como flúor, oxígeno o nitrógeno.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="Debe ocurrir una transferencia neta de electrones hacia un catión metálico de transición.",
                is_correct=False,
                misconception_explanation="Eso caracteriza al enlace iónico o metálico.",
            ),
            QuestionOptionDraft(
                text="Los átomos participantes deben poseer idéntica electronegatividad sin formación de dipolos.",
                is_correct=False,
                misconception_explanation="La polaridad es indispensable para el puente de hidrógeno.",
            ),
            QuestionOptionDraft(
                text="El hidrógeno debe interactuar exclusivamente con átomos de carbono en cadenas alifáticas apolares.",
                is_correct=False,
                misconception_explanation="Los enlaces C-H son poco polares y no forman puentes de hidrógeno significativos.",
            ),
        ],
        explanation="Los puentes de hidrógeno requieren átomos muy electronegativos y pequeños (F, O, N) con pares libres.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.SLIDE,
                index=3,
                snippet="cuando el hidrógeno está unido covalentemente a átomos pequeños y muy electronegativos como flúor, oxígeno o nitrógeno (F, O, N)",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-04-qui-enlace",
        name="enlace_quimico_pptx",
        subject="Química",
        topic="Enlace Químico y Fuerzas Intermoleculares",
        format="pptx",
        total_units=3,
        complexity_level="básico",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 5. BIOLOGÍA: Bioenergética y Respiración Celular (PPTX, 3 diapositivas, avanzada)
# ==============================================================================
def get_cellular_respiration_pptx_benchmark() -> BenchmarkItem:
    """PPTX Benchmark: 3-slide curriculum presentation on cellular respiration."""
    slide1_text = (
        "La glucólisis es la ruta metabólica inicial que se desarrolla en el citosol celular. "
        "Consiste en la degradación anaeróbica de una molécula de glucosa de seis carbonos en dos moléculas de piruvato. "
        "Durante este proceso se produce una ganancia neta de 2 moléculas de ATP y 2 moléculas de NADH por fosforilación a nivel de sustrato."
    )
    slide2_text = (
        "El ciclo de Krebs o ciclo del ácido cítrico se lleva a cabo en la matriz mitocondrial. "
        "El piruvato se descarboxila a acetil-CoA, ingresando al ciclo para oxidarse completamente a dióxido de carbono. "
        "Se generan cofactores reducidos esenciales: NADH y FADH2, encargados de transportar electrones de alta energía."
    )
    slide3_text = (
        "La fosforilación oxidativa ocurre a través de complejos proteicos embebidos en la membrana mitocondrial interna. "
        "El flujo de electrones por la cadena respiratoria bombea protones hacia el espacio intermembrana, creando un gradiente electroquímico. "
        "La enzima ATP sintasa aprovecha la fuerza protón-motriz para sintetizar la mayor parte del ATP celular mediante quimiosmosis."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PPTX,
        original_filename="respiracion_mitocondrial.pptx",
        total_units=3,
        units=[
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=1, text=slide1_text),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=2, text=slide2_text),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=3, text=slide3_text),
        ],
    )

    ref_q1 = GeneratedQuestionDraft(
        suggested_kc_name="Fosforilación Oxidativa",
        question_text="¿Cuál es el mecanismo directo utilizado por la ATP sintasa en la membrana mitocondrial interna para sintetizar ATP?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.600,
        bloom_taxonomy=BloomTaxonomy.ANALYZE,
        options=[
            QuestionOptionDraft(
                text="Aprovecha la fuerza protón-motriz generada por el gradiente electroquímico de protones mediante quimiosmosis.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="Fosforila ADP capturando electrones libres que se desprenden directamente de la glucólisis citosólica.",
                is_correct=False,
                misconception_explanation="Confusión sobre el origen del potencial que impulsa la síntesis de ATP en la mitocondria.",
            ),
            QuestionOptionDraft(
                text="Descarboxila el piruvato para liberar energía mecánica sin participación de gradientes de protones.",
                is_correct=False,
                misconception_explanation="Atribución de la función de descarboxilación del piruvato a la ATP sintasa.",
            ),
            QuestionOptionDraft(
                text="Oxida directamente el dióxido de carbono disuelto en el espacio intermembrana.",
                is_correct=False,
                misconception_explanation="Inversión bioquímica de los productos finales de la respiración celular.",
            ),
        ],
        explanation="La ATP sintasa utiliza el retorno de protones a través de la membrana mitocondrial interna a favor del gradiente electroquímico para catalizar la adición de fosfato inorgánico al ADP.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.SLIDE,
                index=3,
                snippet="La enzima ATP sintasa aprovecha la fuerza protón-motriz para sintetizar la mayor parte del ATP celular mediante quimiosmosis",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-05-bio-resp",
        name="respiracion_pptx",
        subject="Biología",
        topic="Bioenergética, Respiración Celular y Función Mitocondrial",
        format="pptx",
        total_units=3,
        complexity_level="avanzado",
        version="1.0",
        document=doc,
        reference_questions=[ref_q1],
    )


# ==============================================================================
# 6. BIOLOGÍA: Genética Molecular y ADN (PDF, 5 páginas, avanzada)
# ==============================================================================
def get_molecular_genetics_pdf_benchmark() -> BenchmarkItem:
    """PDF Benchmark: 5-page curriculum on molecular genetics and protein synthesis."""
    u1 = (
        "El ácido desoxirribonucleico (ADN) está constituido por dos cadenas de polinucleótidos antiparalelas enrolladas "
        "en una doble hélice dextrógira. Cada nucleótido comprende una base nitrogenada, una desoxirribosa y un grupo fosfato. "
        "Las reglas de equivalencia de Chargaff demuestran que la proporción molar de adenina siempre iguala a la de timina (A = T), "
        "y la guanina iguala a la citosina (G = C) mediante dos y tres enlaces puente de hidrógeno respectivamente."
    )
    u2 = (
        "La replicación del ADN es un proceso semiconservativo donde cada cadena parental sirve de molde para sintetizar una nueva hebra hija. "
        "La enzima helicasa desenrolla la doble hélice en la horquilla de replicación, mientras que la ADN polimerasa cataliza la polimerización "
        "de nuevos nucleótidos exclusivamente en dirección 5' a 3', originando una cadena conductora continua y una cadena rezagada discontinua "
        "formada por fragmentos de Okazaki unidos por la ADN ligasa."
    )
    u3 = (
        "La transcripción genética convierte la información de un gen en una molécula de ARN mensajero (ARNm) precursor dentro del núcleo. "
        "La ARN polimerasa se une a secuencias promotoras específicas y sintetiza ARN sustituyendo la timina por uracilo (U). "
        "El procesamiento postranscripcional incluye la adición de la caperuza 5', la cola de poliadenilación en 3' y el corte y empalme (splicing) "
        "donde se eliminan intrones no codificantes y se ligan los exones codificantes."
    )
    u4 = (
        "El código genético es el conjunto universal y degenerado de reglas que traduce secuencias de tripletes de nucleótidos o codones "
        "del ARNm en aminoácidos específicos. De los 64 codones posibles, 61 codifican para aminoácidos y tres son señales de parada o término "
        "(UAA, UAG, UGA). El codón AUG cumple una doble función esencial: codifica para el aminoácido metionina y actúa como señal universal de inicio."
    )
    u5 = (
        "La traducción de proteínas tiene lugar en los ribosomas citosólicos asociados o libres. "
        "Los ARN de transferencia (ARNt) transportan aminoácidos específicos emparejando sus anticodones con los codones del ARNm. "
        "La peptidil transferasa del ribosoma cataliza la formación de enlaces peptídicos durante la fase de elongación, "
        "hasta que un factor de liberación reconoce un codón de parada y libera la cadena polipeptídica terminada."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PDF,
        original_filename="genetica_molecular_5to.pdf",
        total_units=5,
        units=[
            ExtractedUnit(type=DocumentUnitType.PAGE, index=1, text=u1),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=2, text=u2),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=3, text=u3),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=4, text=u4),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=5, text=u5),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Código Genético y Codón de Inicio",
        question_text="¿Cuál es la doble función primordial que desempeña el codón AUG en el proceso de traducción del ARN mensajero?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.520,
        bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
        options=[
            QuestionOptionDraft(
                text="Codifica para el aminoácido metionina y actúa como la señal universal de inicio de la traducción.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="Actúa como codón de parada y libera el péptido del ribosoma.",
                is_correct=False,
                misconception_explanation="Los codones de parada son UAA, UAG y UGA.",
            ),
            QuestionOptionDraft(
                text="Señala el sitio donde la helicasa inicia el corte de la doble hélice de ADN.",
                is_correct=False,
                misconception_explanation="Confusión entre replicación de ADN y traducción proteica.",
            ),
            QuestionOptionDraft(
                text="Promueve la adición de la cola de poliadenilación en el extremo 3' del transcripto.",
                is_correct=False,
                misconception_explanation="La poliadenilación es parte del procesamiento postranscripcional nuclear.",
            ),
        ],
        explanation="AUG especifica el inicio de la síntesis proteica incorporando metionina en la primera posición del polipéptido.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=4,
                snippet="El codón AUG cumple una doble función esencial: codifica para el aminoácido metionina y actúa como señal universal de inicio",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-06-bio-gen",
        name="genetica_molecular_pdf",
        subject="Biología",
        topic="Genética Molecular, Replicación del ADN y Síntesis de Proteínas",
        format="pdf",
        total_units=5,
        complexity_level="avanzado",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 7. HISTORIA: Revolución Industrial (PDF, 4 páginas, intermedia)
# ==============================================================================
def get_industrial_revolution_pdf_benchmark() -> BenchmarkItem:
    """PDF Benchmark: 4-page curriculum on the Industrial Revolution."""
    u1 = (
        "La Primera Revolución Industrial se originó en Gran Bretaña hacia la segunda mitad del siglo XVIII. "
        "Fue impulsada por la aplicación práctica de la máquina de vapor perfeccionada por James Watt y el aprovechamiento masivo "
        "del carbón mineral como fuente energética primordial para la metalurgia y la industria textil algodonera."
    )
    u2 = (
        "La mecanización de la manufactura modificó radicalmente la estructura social europea. Surgió el proletariado fabril urbano "
        "a raíz del éxodo masivo de campesinos desposeídos tras los cercamientos de tierras comunales (enclosure acts). "
        "Las jornadas de trabajo extenuantes de hasta 16 horas diarias y las pésimas condiciones de salubridad provocaron severas crisis humanitarias."
    )
    u3 = (
        "Hacia fines del siglo XIX, la Segunda Revolución Industrial extendió la transformación productiva a Alemania y Estados Unidos. "
        "Las nuevas fuentes de energía, el petróleo y la electricidad, impulsaron industrias químicas, automotrices y siderúrgicas avanzadas, "
        "dando paso al capitalismo financiero y a métodos de producción en cadena como el fordismo y el taylorismo."
    )
    u4 = (
        "Frente a la explotación industrial, la clase trabajadora organizó los primeros sindicatos y movimientos de resistencia obrera como "
        "el ludismo y el cartismo. Con el tiempo, la presión social y las corrientes ideológicas como el socialismo y la doctrina social de la Iglesia "
        "forzaron la promulgación de las primeras leyes de protección laboral y reducción de jornada en Europa."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PDF,
        original_filename="revolucion_industrial_historia.pdf",
        total_units=4,
        units=[
            ExtractedUnit(type=DocumentUnitType.PAGE, index=1, text=u1),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=2, text=u2),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=3, text=u3),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=4, text=u4),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Fuentes Energéticas de la Segunda Revolución Industrial",
        question_text="¿Cuáles fueron las nuevas fuentes de energía primordiales que caracterizaron la Segunda Revolución Industrial hacia fines del siglo XIX?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.350,
        bloom_taxonomy=BloomTaxonomy.REMEMBER,
        options=[
            QuestionOptionDraft(
                text="El petróleo y la electricidad.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="La energía nuclear y los paneles solares fotovoltaicos.",
                is_correct=False,
                misconception_explanation="Pertenecen al siglo XX y XXI.",
            ),
            QuestionOptionDraft(
                text="El carbón vegetal y la fuerza hidráulica exclusivamente.",
                is_correct=False,
                misconception_explanation="Fueron las fuentes principales de la etapa preindustrial y Primera Revolución.",
            ),
            QuestionOptionDraft(
                text="El gas natural comprimido y el hidrógeno verde.",
                is_correct=False,
                misconception_explanation="Son tecnologías modernas contemporáneas.",
            ),
        ],
        explanation="La Segunda Revolución Industrial se caracterizó por la electrificación y la refinación del petróleo.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=3,
                snippet="Las nuevas fuentes de energía, el petróleo y la electricidad, impulsaron industrias químicas, automotrices y siderúrgicas",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-07-his-revol",
        name="revolucion_industrial_pdf",
        subject="Historia",
        topic="Revolución Industrial y Transformaciones Socioeconómicas Globales",
        format="pdf",
        total_units=4,
        complexity_level="intermedio",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 8. HISTORIA: Segunda Guerra Mundial (PPTX, 5 diapositivas, avanzada)
# ==============================================================================
def get_world_war_two_pptx_benchmark() -> BenchmarkItem:
    """PPTX Benchmark: 5-slide curriculum on World War II and postwar order."""
    s1 = (
        "Las causas de la Segunda Guerra Mundial residen en las severas imposiciones del Tratado de Versalles de 1919, "
        "el colapso económico mundial provocado por la Gran Depresión de 1929 y el ascenso agresivo de regímenes totalitarios fascistas "
        "en Alemania, Italia y Japón. El expansionismo territorial nazi sobre Renania, Austria y Checoslovaquia precipitó la invasión de Polonia en 1939."
    )
    s2 = (
        "El conflicto bélico confrontó a dos bloques militares globales: las Potencias del Eje (Alemania, Italia, Japón) frente a los Aliados "
        "(liderados inicialmente por Gran Bretaña y Francia, a los que se sumaron la Unión Soviética y Estados Unidos en 1941). "
        "La táctica bélica alemana de la 'Blitzkrieg' o guerra relámpago combinó tanques blindados y aviación para arrollar rápidamente a las defensas enemigas."
    )
    s3 = (
        "La guerra generó un costo humano sin precedentes en la historia contemporánea, estimándose en más de 60 millones de víctimas mortales. "
        "El régimen nazi perpetró el Holocausto o 'Solución Final', un genocidio industrializado sistemático que exterminó a más de seis millones de judíos, "
        "además de gitanos, opositores políticos y personas con discapacidad en campos de concentración y exterminio."
    )
    s4 = (
        "En las conferencias interaliadas de Yalta y Potsdam en 1945, las potencias vencedoras acordaron la desmilitarización y división de Alemania "
        "en cuatro zonas de ocupación. Asimismo, para salvaguardar la paz internacional y evitar futuras guerras mundiales, se fundó en San Francisco "
        "la Organización de las Naciones Unidas (ONU), dotada de un Consejo de Seguridad con derecho a veto para las potencias hegemónicas."
    )
    s5 = (
        "El desenlace del conflicto aceleró el declive de las potencias coloniales de Europa occidental y dio inicio a un nuevo orden geopolítico bipolar. "
        "El mundo quedó dividido ideológica y militarmente entre dos superpotencias antagónicas: Estados Unidos (bloque capitalista y OTAN) "
        "y la Unión Soviética (bloque comunista y Pacto de Varsovia), marcando el estallido de la Guerra Fría."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PPTX,
        original_filename="segunda_guerra_mundial_5to.pptx",
        total_units=5,
        units=[
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=1, text=s1),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=2, text=s2),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=3, text=s3),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=4, text=s4),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=5, text=s5),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Conferencias de Paz y Creación de la ONU",
        question_text="¿Cuál fue uno de los principales acuerdos diplomáticos adoptados por los Aliados en 1945 para salvaguardar la paz internacional tras la Segunda Guerra Mundial?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.480,
        bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
        options=[
            QuestionOptionDraft(
                text="La fundación de la Organización de las Naciones Unidas (ONU) con un Consejo de Seguridad dotado de derecho a veto.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="La creación inmediata de la Unión Europea y el establecimiento de la moneda única.",
                is_correct=False,
                misconception_explanation="La integración económica europea ocurrió décadas más tarde.",
            ),
            QuestionOptionDraft(
                text="El restablecimiento de la Sociedad de Naciones en Ginebra bajo mandato británico.",
                is_correct=False,
                misconception_explanation="La Sociedad de Naciones fracasó y fue reemplazada por la ONU.",
            ),
            QuestionOptionDraft(
                text="La anexión militar permanente de Japón como territorio dependiente soviético.",
                is_correct=False,
                misconception_explanation="Japón fue ocupado por fuerzas estadounidenses dirigidas por MacArthur.",
            ),
        ],
        explanation="En la Conferencia de San Francisco en 1945 se creó la ONU para reemplazar a la extinta Sociedad de Naciones.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.SLIDE,
                index=4,
                snippet="se fundó en San Francisco la Organización de las Naciones Unidas (ONU), dotada de un Consejo de Seguridad con derecho a veto",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-08-his-sgm",
        name="segunda_guerra_mundial_pptx",
        subject="Historia",
        topic="Segunda Guerra Mundial y Nuevo Orden Geopolítico de Posguerra",
        format="pptx",
        total_units=5,
        complexity_level="avanzado",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 9. FILOSOFÍA Y CIUDADANÍA: Ética y Democracia (PDF, 3 páginas, básica)
# ==============================================================================
def get_ethics_citizenship_pdf_benchmark() -> BenchmarkItem:
    """PDF Benchmark: 3-page curriculum on ethics, human rights, and constitutional law."""
    u1 = (
        "La ética cívica se fundamenta en el reconocimiento universal de la dignidad intrínseca de la persona humana. "
        "A diferencia de las normas jurídicas coactivas, los imperativos éticos apelan a la autonomía moral y la responsabilidad reflexiva. "
        "En una sociedad pluralista, el bien común se construye mediante la deliberación democrática y el respeto por los derechos inalienables de las minorías."
    )
    u2 = (
        "La Declaración Universal de los Derechos Humanos, aprobada por la Asamblea General de la ONU en 1948, consagró que toda persona nace "
        "libre e igual en dignidad y derechos. La doctrina jurídica clasifica estos derechos en tres generaciones complementarias: "
        "primera generación (derechos civiles y políticos individuales), segunda generación (derechos económicos, sociales y culturales) "
        "y tercera generación (derechos colectivos de solidaridad de los pueblos, como la paz y el medio ambiente sano)."
    )
    u3 = (
        "El Estado constitucional de derecho descansa sobre el principio insoslayable de separación de poderes formulado por Montesquieu. "
        "El poder público se distribuye entre los poderes Ejecutivo, Legislativo y Judicial, estableciendo un sistema de pesos y contrapesos (checks and balances). "
        "La Constitución ostenta supremacía normativa sobre cualquier ley o disposición jerárquicamente inferior, garantizada por órganos de control constitucional."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PDF,
        original_filename="etica_derechos_constitucion.pdf",
        total_units=3,
        units=[
            ExtractedUnit(type=DocumentUnitType.PAGE, index=1, text=u1),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=2, text=u2),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=3, text=u3),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Generaciones de Derechos Humanos",
        question_text="¿Qué ámbito de protección abarca la segunda generación de derechos humanos según la doctrina jurídica?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.320,
        bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
        options=[
            QuestionOptionDraft(
                text="Derechos económicos, sociales y culturales.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="Derechos civiles y políticos individuales de libertad.",
                is_correct=False,
                misconception_explanation="Pertenecen a la primera generación surgida en las revoluciones liberales.",
            ),
            QuestionOptionDraft(
                text="Derechos de solidaridad de los pueblos y preservación ambiental.",
                is_correct=False,
                misconception_explanation="Corresponden a la tercera generación de derechos humanos.",
            ),
            QuestionOptionDraft(
                text="Derechos de propiedad comercial de patentes industriales.",
                is_correct=False,
                misconception_explanation="La propiedad industrial está regulada por el derecho comercial ordinario.",
            ),
        ],
        explanation="La segunda generación garantiza el acceso a la salud, educación, trabajo digno y seguridad social.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=2,
                snippet="segunda generación (derechos económicos, sociales y culturales)",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-09-fil-etica",
        name="etica_ciudadania_pdf",
        subject="Filosofía y Ciudadanía",
        topic="Ética, Derechos Humanos y Principios Constitucionales",
        format="pdf",
        total_units=3,
        complexity_level="básico",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 10. ECOLOGÍA: Ciclos Biogeoquímicos y Clima (PPTX, 4 diapositivas, intermedia)
# ==============================================================================
def get_ecology_climate_pptx_benchmark() -> BenchmarkItem:
    """PPTX Benchmark: 4-slide curriculum on biogeochemical cycles and climate change."""
    s1 = (
        "El ciclo del carbono regula el equilibrio termodinámico de la biosfera a través de intercambios continuos de carbono entre "
        "la atmósfera, los océanos, la litosfera y los seres vivos. La fotosíntesis oxigénica fija dióxido de carbono (CO2) inorgánico en biomasa, "
        "mientras que la respiración celular y la descomposición orgánica devuelven carbono a la atmósfera en forma de CO2 y metano (CH4)."
    )
    s2 = (
        "El ciclo del nitrógeno depende estrictamente de la actividad metabólica de bacterias especializadas en el suelo y nódulos radiculares. "
        "El nitrógeno gaseoso atmosférico (N2), que constituye el 78% del aire, no puede ser asimilado directamente por las plantas. "
        "Bacterias fijadoras como Rhizobium lo transforman en amonio (NH4+), que luego es oxidado por bacterias nitrificantes en nitritos y nitratos absorbibles."
    )
    s3 = (
        "El efecto invernadero es un fenómeno físico natural beneficioso que mantiene la temperatura media planetaria en aproximadamente 15 °C. "
        "Sin embargo, la combustión a gran escala de hidrocarburos fósiles y la deforestación masiva han incrementado la concentración atmosférica "
        "de gases de efecto invernadero (GEI), atrapando radiación infrarroja saliente y provocando el calentamiento global antropogénico acelerado."
    )
    s4 = (
        "La mitigación del cambio climático exige la transición urgente hacia una matriz energética descarbonizada basada en fuentes renovables "
        "(solar, eólica, geotérmica) y la conservación de sumideros naturales de carbono como bosques tropicales y humedales. "
        "La adaptación climática comprende obras de infraestructura resiliente, tecnificación del riego agrícola y sistemas de alerta temprana ante desastres."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PPTX,
        original_filename="ecologia_ciclos_clima.pptx",
        total_units=4,
        units=[
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=1, text=s1),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=2, text=s2),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=3, text=s3),
            ExtractedUnit(type=DocumentUnitType.SLIDE, index=4, text=s4),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Fijación Biológica del Nitrógeno",
        question_text="¿Por qué la fijación bacteriana es indispensable para que las plantas puedan utilizar el nitrógeno en su nutrición?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.420,
        bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
        options=[
            QuestionOptionDraft(
                text="Porque el nitrógeno gaseoso atmosférico (N2) no puede ser asimilado directamente y requiere transformarse en compuestos asimilables.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="Porque las bacterias consumen nitrógeno para sintetizar clorofila directamente dentro del tallo.",
                is_correct=False,
                misconception_explanation="Las bacterias no producen clorofila para las plantas superiores.",
            ),
            QuestionOptionDraft(
                text="Porque el nitrógeno en la atmósfera se encuentra en concentraciones mínimas menores al 1%.",
                is_correct=False,
                misconception_explanation="El nitrógeno representa el 78% del volumen de la atmósfera terrestre.",
            ),
            QuestionOptionDraft(
                text="Porque el suelo carece de minerales y solo las bacterias generan oxígeno.",
                is_correct=False,
                misconception_explanation="Confusión de ciclos biogeoquímicos con fotosíntesis.",
            ),
        ],
        explanation="Las plantas solo pueden absorber nitrógeno inorgánico en forma de iones amonio o nitrato, producidos por fijación y nitrificación bacteriana.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.SLIDE,
                index=2,
                snippet="El nitrógeno gaseoso atmosférico (N2), que constituye el 78% del aire, no puede ser asimilado directamente por las plantas. Bacterias fijadoras como Rhizobium lo transforman en amonio",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-10-eco-ciclos",
        name="ecologia_cambio_climatico_pptx",
        subject="Ecología",
        topic="Ciclos Biogeoquímicos y Mitigación del Cambio Climático",
        format="pptx",
        total_units=4,
        complexity_level="intermedio",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# 11. GEOGRAFÍA: Cuencas Hidrográficas y Riesgos en el Perú (PDF, 3 páginas, básica)
# ==============================================================================
def get_geography_watersheds_pdf_benchmark() -> BenchmarkItem:
    """PDF Benchmark: 3-page curriculum on Peruvian hydrology and disaster risk management."""
    u1 = (
        "El territorio peruano está modelado por la Cordillera de los Andes, que actúa como divisoria continental de aguas "
        "originando tres grandes vertientes hidrográficas: la vertiente del Pacífico (ríos cortos, torrentosos y de régimen irregular), "
        "la vertiente del Atlántico o cuenca amazónica (ríos caudalosos, navegables y de curso meándrico) y la hoya del Lago Titicaca "
        "(cuenca endorreica cerrada de gran altitud)."
    )
    u2 = (
        "El Fenómeno de El Niño (FEN) es una anomalía oceánico-atmosférica caracterizada por el calentamiento inusual de las aguas del Pacífico "
        "ecuatorial y la costa norte del Perú. Provoca lluvias torrenciales extraordinarias en la vertiente occidental, desbordes fluviales "
        "e inundaciones masivas en los departamentos de Piura, Lambayeque y La Libertad, contrastando con severas sequías en el altiplano sur."
    )
    u3 = (
        "La Gestión del Riesgo de Desastres (GRD) en el marco de la Ley N° 29664 en el Perú articula tres componentes estratégicos: "
        "la gestión prospectiva (planificación territorial para evitar nuevos riesgos), la gestión correctiva (mitigación de vulnerabilidades existentes) "
        "y la gestión reactiva (preparación y respuesta ante emergencias). El ordenamiento de fajas marginales de los ríos es prioritario para evitar pérdidas humanas."
    )

    doc = ExtractedDocument(
        document_type=DocumentType.PDF,
        original_filename="geografia_cuencas_riesgos_peru.pdf",
        total_units=3,
        units=[
            ExtractedUnit(type=DocumentUnitType.PAGE, index=1, text=u1),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=2, text=u2),
            ExtractedUnit(type=DocumentUnitType.PAGE, index=3, text=u3),
        ],
    )

    ref_q = GeneratedQuestionDraft(
        suggested_kc_name="Componentes de la Gestión del Riesgo de Desastres",
        question_text="¿Cuáles son los tres componentes estratégicos de la Gestión del Riesgo de Desastres regulados por la normativa peruana?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.340,
        bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
        options=[
            QuestionOptionDraft(
                text="Gestión prospectiva, gestión correctiva y gestión reactiva.",
                is_correct=True,
            ),
            QuestionOptionDraft(
                text="Evacuación forzada, reconstrucción financiera y privatización hídrica.",
                is_correct=False,
                misconception_explanation="No corresponden a los componentes doctrinarios de la ley GRD.",
            ),
            QuestionOptionDraft(
                text="Monitoreo satelital, dragado exclusivo y canalización de quebradas.",
                is_correct=False,
                misconception_explanation="Son medidas técnicas operativas pero no componentes estratégicos de la gestión.",
            ),
            QuestionOptionDraft(
                text="Alerta sísmica, socorro humanitario y compensación de daños únicamente.",
                is_correct=False,
                misconception_explanation="Limita la gestión a la fase reactiva omitiendo la prevención prospectiva.",
            ),
        ],
        explanation="La Ley N° 29664 establece la gestión prospectiva (prevenir futuro riesgo), correctiva (reducir riesgo actual) y reactiva (atender emergencias).",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=3,
                snippet="la gestión prospectiva (planificación territorial para evitar nuevos riesgos), la gestión correctiva (mitigación de vulnerabilidades existentes) y la gestión reactiva (preparación y respuesta ante emergencias)",
            )
        ],
    )

    return BenchmarkItem(
        id="bench-11-geo-cuencas",
        name="geografia_gestion_riesgos_pdf",
        subject="Geografía",
        topic="Cuencas Hidrográficas y Gestión de Riesgo de Desastres en el Perú",
        format="pdf",
        total_units=3,
        complexity_level="básico",
        version="1.0",
        document=doc,
        reference_questions=[ref_q],
    )


# ==============================================================================
# Colección completa de benchmarks estandarizados (11 documentos curriculares)
# ==============================================================================
def get_benchmark_documents() -> list[BenchmarkItem]:
    """Return complete suite of 11 curriculum benchmark items for reproducible evaluation."""
    return [
        get_thermodynamics_pdf_benchmark(),
        get_harmonic_motion_pptx_benchmark(),
        get_stoichiometry_pdf_benchmark(),
        get_chemical_bonding_pptx_benchmark(),
        get_cellular_respiration_pptx_benchmark(),
        get_molecular_genetics_pdf_benchmark(),
        get_industrial_revolution_pdf_benchmark(),
        get_world_war_two_pptx_benchmark(),
        get_ethics_citizenship_pdf_benchmark(),
        get_ecology_climate_pptx_benchmark(),
        get_geography_watersheds_pdf_benchmark(),
    ]
