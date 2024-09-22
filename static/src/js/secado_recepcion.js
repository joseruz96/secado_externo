// odoo.define('package_move.package_impale', function (require) {
//     "use strict";

//     var FieldMany2One = require('web.relational_fields').FieldMany2One;

//     FieldMany2One.include({
//         init: function () {
//             this._super.apply(this, arguments);
//             if (this.name === 'package_id') {
//                 this.widget = 'custom_package_id';
//                 console.log("Custom widget applied to package_id field!");

//             }
//         },
//     });
// });
odoo.define('secado_externo.secado_recepcion', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var rpc = require('web.rpc');

    FormController.include({
        events: _.extend({}, FormController.prototype.events, {
            'input input[name="package_input"]': '_onPackageInput',
        }),

        _onPackageInput: function (event) {
            var packageInputValue = event.target.value;

            // Verificar si el último carácter ingresado es un espacio
            setTimeout(function () {
                var lastChar = packageInputValue.slice(-1);
                if (lastChar !== ' ') {
                    // Agregar un espacio al final del valor
                    packageInputValue += ' ';
                    event.target.value = packageInputValue;  // Actualizar el valor en el campo
                }
            }, 500);
        },
    });

    return {
        FormController: FormController,
    };
});
