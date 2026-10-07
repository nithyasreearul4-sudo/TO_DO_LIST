/* =========================================================
   BLOOMTASKS JAVASCRIPT
========================================================= */


/* =========================================================
   COMPLETION POPUP
========================================================= */

function closeCompletionModal() {

    const modal = document.getElementById(
        "completionModal"
    );

    if (modal) {

        modal.style.opacity = "0";

        setTimeout(function () {

            modal.style.display = "none";

        }, 250);
    }
}


/* =========================================================
   CLOSE POPUP WHEN CLICKING OUTSIDE
========================================================= */

document.addEventListener(
    "click",
    function (event) {

        const modal = document.getElementById(
            "completionModal"
        );

        if (
            modal &&
            event.target === modal
        ) {

            closeCompletionModal();
        }

    }
);


/* =========================================================
   ESCAPE KEY
========================================================= */

document.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Escape") {

            closeCompletionModal();

        }

    }
);


/* =========================================================
   AUTO HIDE FLASH MESSAGES
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const messages =
            document.querySelectorAll(".flash");

        messages.forEach(function (message) {

            setTimeout(function () {

                message.style.opacity = "0";

                message.style.transform =
                    "translateX(20px)";

                message.style.transition =
                    "0.4s";

                setTimeout(function () {

                    message.remove();

                }, 400);

            }, 4000);

        });

    }
);