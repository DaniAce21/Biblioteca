// JavaScript del Sistema de Biblioteca.
// Los comentarios explican los eventos y comportamientos implementados.

/* ================================================================
   REGISTRO DE USUARIO - JAVASCRIPT
   ----------------------------------------------------------------
   Controla los pasos del formulario y la visibilidad de sus botones.
   ================================================================ */

/* =============================================================
       SISTEMA DE PASOS
       ============================================================= */

    let currentStep = 1;


    const totalSteps = 3;


    const form = document.getElementById(
        "registerForm"
    );


    const nextButton = document.getElementById(
        "nextButton"
    );


    const backButton = document.getElementById(
        "backButton"
    );


    const createButton = document.getElementById(
        "createButton"
    );


    function showStep(step) {

        /* ---------------------------------------------------------
           Ocultar todas las capas
           --------------------------------------------------------- */

        document
            .querySelectorAll(".step-content")
            .forEach(function(element) {

                element.classList.remove("active");

            });


        /* ---------------------------------------------------------
           Mostrar capa actual
           --------------------------------------------------------- */

        document
            .getElementById(
                "step" + step
            )
            .classList.add("active");


        /* ---------------------------------------------------------
           Actualizar indicadores
           --------------------------------------------------------- */

        for (
            let i = 1;
            i <= totalSteps;
            i++
        ) {

            const indicator =
                document.getElementById(
                    "stepIndicator" + i
                );


            indicator.classList.remove(
                "active"
            );


            indicator.classList.remove(
                "completed"
            );


            if (i === step) {

                indicator.classList.add(
                    "active"
                );

            }


            if (i < step) {

                indicator.classList.add(
                    "completed"
                );

            }

        }


        /* ---------------------------------------------------------
           Botón atrás
           --------------------------------------------------------- */

        if (step === 1) {

            backButton.classList.add(
                "is-hidden"
            );

        } else {

            backButton.classList.remove(
                "is-hidden"
            );

        }


        /* ---------------------------------------------------------
           Botones siguientes / crear
           --------------------------------------------------------- */

        if (step === totalSteps) {

            nextButton.classList.add(
                "is-hidden"
            );

            createButton.classList.remove(
                "is-hidden"
            );

        } else {

            nextButton.classList.remove(
                "is-hidden"
            );

            createButton.classList.add(
                "is-hidden"
            );

        }


        /* ---------------------------------------------------------
           Scroll arriba
           --------------------------------------------------------- */

        window.scrollTo({

            top: 0,

            behavior: "smooth"

        });

    }


    /* =============================================================
       SIGUIENTE
       ============================================================= */

    function nextStep() {

        if (currentStep < totalSteps) {

            currentStep++;

            showStep(
                currentStep
            );

        }

    }


    /* =============================================================
       ATRÁS
       ============================================================= */

    function previousStep() {

        if (currentStep > 1) {

            currentStep--;

            showStep(
                currentStep
            );

        }

    }


    /* =============================================================
       SI DJANGO DEVUELVE ERRORES
       ============================================================= */

    document.addEventListener(
        "DOMContentLoaded",
        function() {

            const hasErrors =
                document.querySelector(
                    ".error-list, .global-error"
                );


            if (hasErrors) {

                /*
                 * Si hay errores de contraseña,
                 * mostramos directamente el paso 3.
                 */

                const passwordErrors =
                    document.querySelector(
                        "#id_password + .error-list, " +
                        "#id_password_confirm + .error-list"
                    );


                if (passwordErrors) {

                    currentStep = 3;

                    showStep(
                        currentStep
                    );

                }

            }

        }
    );
