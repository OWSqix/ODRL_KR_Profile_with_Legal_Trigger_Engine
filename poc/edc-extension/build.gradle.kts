plugins {
    java
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
}

tasks.test {
    dependsOn("testClasses")
    doLast {
        javaexec {
            classpath = sourceSets["main"].runtimeClasspath + sourceSets["test"].runtimeClasspath
            mainClass.set("org.odrlkr.edc.KoreaPolicyFunctionTest")
        }
    }
}
