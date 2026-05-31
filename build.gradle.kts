import org.asciidoctor.gradle.jvm.pdf.AsciidoctorPdfTask

plugins {
    id("org.asciidoctor.jvm.pdf") version "4.0.4"
}

repositories {
    mavenCentral()
}

asciidoctorj {
    // Rendert [mermaid]-Blöcke beim Build via lokalem mmdc (offline, kein Netzwerk)
    modules {
        diagram.use()
    }
}

// Erzeugt build/docs/asciidocPdf/konzept.pdf und praesentation.pdf
tasks.named<AsciidoctorPdfTask>("asciidoctorPdf") {
    group = "documentation"
    description = "Erzeugt Konzept- und Präsentations-PDF aus docs/ (inkl. Mermaid-Diagramme)."

    baseDirFollowsSourceFile()
    setSourceDir(file("docs"))
    sources {
        include("konzept.adoc")
        // Folien-Vorlage; Querformat/Folien-Layout steht im Header der Datei.
        include("praesentation.adoc")
    }

    // mmdc/Chromium braucht auf Linux i. d. R. --no-sandbox
    attributes(
        mapOf(
            "mermaid-puppeteer-config" to file("docs/.puppeteer-config.json").absolutePath,
            "mermaid-format" to "png",
            // 3x Pixeldichte (Puppeteer deviceScaleFactor) → scharfe PNGs trotz
            // Hochskalierung auf Folien-/Seitenbreite. Pro-Block via scale=… überschreibbar.
            "mermaid-scale" to "3",
        ),
    )
}
