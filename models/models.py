# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Picking(models.Model):
    _inherit = 'stock.picking'
    
    def button_validate(self):
        result = super(Picking, self).button_validate()
        print("PICKING IN")
        # picking_type = self.env['stock.picking.type'].search([('recepcion_secado_externo', '=', True)])
        picking_type = self.picking_type_id
        if picking_type.produccion_secado_externo:
            # Crear el stock.picking (albarán)
            picking_vals = {
                'partner_id': self.partner_id.id,  # Proveedor o destinatario
                'location_id': picking_type.default_location_src_id.id,  # Ubicación de origen
                'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
                'picking_type_id': picking_type.id,  # Tipo de operación
                'origin': self.name,  # Referencia al documento de origen
                # 'move_lines': [],  # Movimientos (a completar más abajo)
                'package_level_ids_details': [],  # Paquetes asignados
            }
            
            # Crear los movimientos del stock.picking en función de los paquetes de secado
            package_levels = []
            move_lines = []
            for line in self.package_level_ids_details:
                package = line.package_id
                if package:
                    current_quant_ids = package.quant_ids
                    for quant in current_quant_ids:
                        espesor = quant.product_id.espesor
                        ancho = quant.product_id.ancho
                        largo = quant.product_id.largo
                        product = self.env['product.product'].search([('isSecado', '=', True), ('espesor', '=', espesor), ('ancho', '=', ancho), ('largo', '=', largo)])
                        if product:
                            quant.write({'product_id': product.id})
                            move_vals = {
                                'product_id': quant.product_id.id,  # Nombre descriptivo de la operación
                                'name': quant.product_id.name,  # Nombre descriptivo de la operación
                                'product_uom_qty': quant.quantity,  # Cantidad 1 ya que estamos moviendo un paquete completo
                                'product_uom': self.env.ref('uom.product_uom_unit').id,  # Unidad de medida como 'unidad'
                                'location_id': picking_type.default_location_src_id.id,  # Ubicación de origen
                                'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
                            }
                            move_lines.append((0, 0, move_vals))  # Añadir el movimiento de paquete
                        else:
                            mensaje_error = f"El producto {quant.product_id.name} no tiene creado el proceso de secado."
                            raise ValidationError(_(mensaje_error))
                        
                    # Crear el nivel de paquete
                    package_level_vals = {
                        'package_id': package.id,  # Paquete a mover
                        'is_done': True,  # Paquete a mover
                        'company_id': self.env.company.id,
                        'location_id': picking_type.default_location_src_id.id,  # Ubicación de origen
                        'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
                        # 'picking_id': self.picking_id.id,  # ID del picking relacionado
                    }
                    package_levels.append((0, 0, package_level_vals))  # Añadir nivel de paquete

            # Asignar las líneas de movimiento y los niveles de paquete al picking
            # picking_vals['move_lines'] = move_lines
            picking_vals['move_lines'] = move_lines
            picking_vals['package_level_ids_details'] = package_levels
                
        return result   
        

class SecadoFormulario(models.Model):
    _name = 'secado_externo.secado_formulario'
    _rec_name = 'id'
    
    partner_id = fields.Many2one(
        'res.partner', 
        'Proveedor Servicio',
        state={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    partner_child_id = fields.Many2one(
        'res.partner', 
        string="Ubicación Destino",
        state={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain="[('parent_id', '=', partner_id)]",
    )
    
    secado_paquetes_ids = fields.One2many(
        "secado_externo.secado_paquetes", 'secado_formulario_id'
    )
    
    picking_type_id = fields.Many2one(
        'stock.picking.type', 
        string='Tipo Operación',
        required=True, 
        domain="[('produccion_secado_externo', '=', True)]",
        default=lambda self: self.env['stock.picking.type'].search([('produccion_secado_externo', '=', True)], limit=1),
        states={'draft': [('readonly', False)]}
    )
    
    picking_id = fields.Many2one(
        'stock.picking', 
        string="Albarán", 
        readonly=True
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        related='picking_type_id.company_id',
        readonly=True, 
        store=True,
    )
    
    
    date = fields.Datetime(
        'Fecha Creación',
        default=fields.Datetime.now, tracking=True,
        state={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Creation Date, usually the time of the order"
    )
    
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('done', 'Despachado'),
            ('cancel', 'Cancelado'),
        ],
        default='draft'
    )
    
    price_per_pul = fields.Float(string='Valor por Pulgada',  digits=(16,2))
    total_pul = fields.Float(string='Pulgadas',  digits=(16,2))
    flete = fields.Float(string='Flete',  digits=(16,2))
    impuesto = fields.Float(string='IVA 19%',  digits=(16,2))
    subtotal_price = fields.Float(string='Precio Subtotal',  digits=(16,2))
    total_price = fields.Float(string='Precio Total',  digits=(16,2))
    origin = fields.Char(string='Origen')
    doc_origin = fields.Char(string='Documento Origen')
    quantity = fields.Float(string='Cantidad de Piezas Despachadas')
    chofer = fields.Char('Nombre Chofer')
    chofer_rut = fields.Char('RUT Chofer')
    patente_camion = fields.Char('Patente Camión')
    patente_carro = fields.Char('Patente Carro')
    documentos = fields.Many2many('ir.attachment', string="Adjuntar Documentos")
    package_count = fields.Integer(string="Cantidad de Paquetes Despachados")
    picking_count = fields.Integer(string='Cantidad de Despachos', compute='_compute_picking_count')

    name = fields.Char(string='Secado Formulario', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        # Crear el registro primero
        secado_formulario = super(SecadoFormulario, self).create(vals)

        # Asignar el nombre con el ID del nuevo registro
        secado_formulario.name = f'DESP/SEC/EXT/{secado_formulario.id}'

        # Retornar el registro con el nombre actualizado
        return secado_formulario

        
    def action_view_pickings(self):
        pickings = self.env['stock.picking'].search([('origin', '=', self.name)])
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif len(pickings) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _compute_picking_count(self):
        for record in self:
            record.picking_count = self.env['stock.picking'].search_count([
                ('origin', '=', record.name)
            ])

    def action_confirm(self):
        if self.picking_type_id.produccion_secado_externo:
            self.compute_pul()
            self.compute_total_price()
        self.create_stock_picking()
    
    def compute_pul(self):
        for rec in self.secado_paquetes_ids:
            self.quantity += rec.quantity
            self.total_pul += rec.pul

            
    def compute_total_price(self):
        self.subtotal_price = self.price_per_pul * self.total_pul + self.flete
        self.impuesto = self.subtotal_price * 0.19
        self.total_price = self.subtotal_price + self.impuesto
        
    def create_stock_picking(self):
        # Obtener el stock.picking.type desde picking_type_id
        picking_type = self.picking_type_id
        location = ''
        secado_ids = ''
        if self.picking_type_id.produccion_secado_externo:
            location = self.env['stock.location'].search([('secador_location', '=', True)])
            secado_ids = self.secado_paquetes_ids
        else:
            location = self.env['stock.location'].search([('produccion_secado_externo', '=', True)]) 
            secado_ids = self.secado_recepcion_ids
        picking_vals = {
            # 'name': f'Secad/IN/{self.id}',  # Asegúrate de que sea único
            'partner_id': self.partner_id.id,  # Proveedor o destinatario
            'location_id': location.id,  # Ubicación de origen
            'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
            'picking_type_id': picking_type.id,  # Tipo de operación
            'origin': self.name,  # Referencia al documento de origen
            # 'move_lines': [],  # Movimientos (a completar más abajo)
            'chofer': self.chofer,  # Ubicación de destino
            'rut_chofer': self.chofer_rut,  # Ubicación de destino
            'patente_camion': self.patente_camion,  # Ubicación de destino
            'patente_carro': self.patente_carro,  # Ubicación de destino
            'precio_flete': self.flete,  # Ubicación de destino
            'amount_untaxed': self.subtotal_price,  # Ubicación de destino
            'amount_tax': self.impuesto,  # Ubicación de destino
            'amount_total': self.total_price,  # Ubicación de destino
            'package_level_ids_details': [],  # Paquetes asignados
        }
        
        package_levels = []
        move_lines = []
        for secado_paquete in secado_ids:
            package = secado_paquete.package_id
            if package:
                current_quant_ids = package.quant_ids
                move_vals = {
                    'product_id': current_quant_ids.product_id.id,  # Nombre descriptivo de la operación
                    'name': current_quant_ids.product_id.name,  # Nombre descriptivo de la operación
                    'product_uom_qty': current_quant_ids.quantity,  # Cantidad 1 ya que estamos moviendo un paquete completo
                    'product_uom': self.env.ref('uom.product_uom_unit').id,  # Unidad de medida como 'unidad'
                    'location_id': location.id,  # Ubicación de origen
                    'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
                }
                move_lines.append((0, 0, move_vals))  # Añadir el movimiento de paquete
                # Crear el nivel de paquete
                package_level_vals = {
                    'package_id': package.id,  # Paquete a mover
                    'company_id': self.env.company.id,
                    'location_id': location.id,  # Ubicación de origen
                    'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
                    'picking_id': self.picking_id.id,  # ID del picking relacionado
                    'is_done': True,  # ID del picking relacionado
                }
                package_levels.append((0, 0, package_level_vals))  # Añadir nivel de paquete
                self.package_count += 1
        # Asignar las líneas de movimiento y los niveles de paquete al picking
        picking_vals['move_lines'] = move_lines
        picking_vals['package_level_ids_details'] = package_levels
        
        # Crear el picking
        picking = self.env['stock.picking'].create(picking_vals)
        
        # Confirmar el picking para que pase del estado 'borrador' a 'confirmado'
        picking.action_confirm()

        # Validar el picking si deseas que también pase al estado 'hecho' directamente
        picking.button_validate()

        # Asociar el picking recién creado con el formulario de secado
        self.picking_id = picking.id

        # Crear la recepción de secado
        self.create_secado_recepcion()
        self.state = 'done'

            
        # Retornar el picking creado para más acciones si es necesario
        return picking
        
    def create_secado_recepcion(self):
        get_paquetes_faltantes = self.get_paquetes_faltantes()
        if get_paquetes_faltantes:
            picking_type = self.env['stock.picking.type'].search([('recepcion_secado_externo', '=', True)], limit=1)
            recepcion_vals = {
                'partner_id': self.partner_id.id,
                'partner_child_id': self.partner_child_id.id,
                'picking_type_id': picking_type.id,
                'package_count': self.package_count,
                'price_per_pul': self.price_per_pul,
                'quantity': self.quantity if self.picking_type_id.produccion_secado_externo else self.quantity - self.quantity_recep,
                'secado_recepcion_ids': [(6, 0, self.get_paquetes_faltantes().ids)],
                'origin': self.name if self.picking_type_id.produccion_secado_externo else self.origin
            }
            
            secado_recepcion = self.env['secado_externo.secado_recepcion'].create(recepcion_vals)
            
            return secado_recepcion
        
    
    def get_paquetes_faltantes(self):
        """
        Obtiene los paquetes que faltan por recepcionar.
        """
        # Obtener los paquetes que están en este formulario de secado
        paquetes_despachados = self.secado_paquetes_ids

        # Buscar todos los paquetes que ya han sido recepcionados en otras secado_recepcion
        recepcionados = self.env['secado_externo.secado_paquetes'].search([
            ('secado_formulario_id.id', '=', self.origin),  # Los que pertenecen a este formulario
            ('secado_recepcion_id', '!=', False)  # Que ya tienen una recepcion
        ])
        print("DESP",paquetes_despachados)
        print("RECEP",recepcionados)
        # Filtrar los paquetes que aún no han sido recepcionados
        paquetes_faltantes = paquetes_despachados - recepcionados

        # Retornar los paquetes faltantes
        return paquetes_faltantes
        
    # def create_stock_picking_in(self, picking):
    #     print("PICKING IN")
    #     picking_type = self.env['stock.picking.type'].search([('recepcion_secado_externo', '=', True)])
        
    #     # Crear el stock.picking (albarán)
    #     picking_vals = {
    #         'partner_id': self.partner_id.id,  # Proveedor o destinatario
    #         'location_id': picking_type.default_location_src_id.id,  # Ubicación de origen
    #         'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
    #         'picking_type_id': picking_type.id,  # Tipo de operación
    #         'origin': picking.origin,  # Referencia al documento de origen
    #         # 'move_lines': [],  # Movimientos (a completar más abajo)
    #         'package_level_ids_details': [],  # Paquetes asignados
    #     }
        
    #     # Crear los movimientos del stock.picking en función de los paquetes de secado
    #     package_levels = []
    #     move_lines = []
    #     for line in picking.package_level_ids_details:
    #         package = line.package_id
    #         if package:
    #             current_quant_ids = package.quant_ids
    #             for quant in current_quant_ids:
    #                 espesor = quant.product_id.espesor
    #                 ancho = quant.product_id.ancho
    #                 largo = quant.product_id.largo
    #                 product = self.env['product.product'].search([('isSecado', '=', True), ('espesor', '=', espesor), ('ancho', '=', ancho), ('largo', '=', largo)])
    #                 if product:
    #                     quant.write({'product_id': product.id})
    #                     move_vals = {
    #                         'product_id': quant.product_id.id,  # Nombre descriptivo de la operación
    #                         'name': quant.product_id.name,  # Nombre descriptivo de la operación
    #                         'product_uom_qty': quant.quantity,  # Cantidad 1 ya que estamos moviendo un paquete completo
    #                         'product_uom': self.env.ref('uom.product_uom_unit').id,  # Unidad de medida como 'unidad'
    #                         'location_id': picking_type.default_location_src_id.id,  # Ubicación de origen
    #                         'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
    #                     }
    #                     move_lines.append((0, 0, move_vals))  # Añadir el movimiento de paquete
    #                 else:
    #                     mensaje_error = f"El producto {quant.product_id.name} no tiene creado el proceso de impregnado."
    #                     raise ValidationError(_(mensaje_error))
                    
    #             # Crear el nivel de paquete
    #             package_level_vals = {
    #                 'package_id': package.id,  # Paquete a mover
    #                 'company_id': self.env.company.id,
    #                 'location_id': picking_type.default_location_src_id.id,  # Ubicación de origen
    #                 'location_dest_id': picking_type.default_location_dest_id.id,  # Ubicación de destino
    #                 'picking_id': self.picking_id.id,  # ID del picking relacionado
    #             }
    #             package_levels.append((0, 0, package_level_vals))  # Añadir nivel de paquete

    #     # Asignar las líneas de movimiento y los niveles de paquete al picking
    #     # picking_vals['move_lines'] = move_lines
    #     picking_vals['move_lines'] = move_lines
    #     picking_vals['package_level_ids_details'] = package_levels
        
    #     # Crear el picking
    #     picking = self.env['stock.picking'].create(picking_vals)
        
    #     # Asociar el picking recién creado con el formulario de secado
    #     # self.picking_id = picking.id
        
    #     return picking

        
class SecadoPaquetes(models.Model):
    _name = 'secado_externo.secado_paquetes'
    
    package_id = fields.Many2one(
        'stock.quant.package', 
        string='Paquete', 
        required=True,
        domain="[('location_id.secador_location', '=', True)]",
    )
    product_id = fields.Many2one('product.product', string='Producto a Transformar', related='package_id.quant_ids.product_id')
    product_name = fields.Char('Producto Original')
    quantity = fields.Float(string='Cantidad', related='package_id.quant_ids.quantity', digits=(16,0))
    pul = fields.Float('Pulgadas', compute='_compute_factor_pulgada')
    secado_formulario_id = fields.Many2one('secado_externo.secado_formulario', string='Formulario Secado')
    recepcionado = fields.Boolean(string='¿Recepcionado?', default=False)
    secado_recepcion_id = fields.Many2one('secado_externo.secado_recepcion', string='Secado Recepción')
    
    @api.onchange('package_id')
    def _compute_product_name(self):
        self.product_name = self.package_id.quant_ids.product_id.name
    
    # @api.onchange('package_id')
    def _compute_factor_pulgada(self):
        for rec in self:
            rec.pul = 0
            factor_pulgada = 0
            print(rec.product_id.product_template_variant_value_ids.name)
            mantenedor = rec.env['stock.mantenedor_cubicacion'].search([('nombre', '=', rec.product_id.product_template_variant_value_ids.name), ('largo', '=', rec.product_id.largo)])
            if mantenedor:
                factor_pulgada = mantenedor.factor
            else:
                factor_pulgada = 1
            if factor_pulgada and rec.quantity and rec.product_id.espesor and rec.product_id.ancho:
                rec.pul = (factor_pulgada * rec.quantity * rec.product_id.espesor * rec.product_id.ancho)/10
            else:
                rec.pul = 0
            

class SecadoRecepcion(models.Model):    
    _name = 'secado_externo.secado_recepcion'
    _inherit = 'secado_externo.secado_formulario'
    
    secado_recepcion_ids = fields.One2many(
        "secado_externo.secado_paquetes", 'secado_recepcion_id'
    )
    
    package_input = fields.Char("Paquete", digits=(16,0))
    quantity_recep = fields.Float(string='Cantidad de Piezas Recepcionadas')

    state_recep = fields.Selection(
        [
            ('nr', 'No Recepcionado'),
            ('rp', 'Recepcionado Parcialemente'),
            ('done', 'Recepcionado'),
            ('cancel', 'Cancelado'),
        ],
        default='nr'
    )
    
    package_count_recep = fields.Integer(string="Cantidad de Paquetes Recepcionados")

    @api.model
    def create(self, vals):
        # Crear el registro primero
        secado_recepcion = super(SecadoRecepcion, self).create(vals)

        # Asignar el nombre con el ID del nuevo registro
        secado_recepcion.name = f'RECEP/SEC/EXT/{secado_recepcion.id}'

        # Retornar el registro con el nombre actualizado
        return secado_recepcion
    
    @api.onchange('package_input')
    def _check_packages(self):
        if self.package_input:
            valores = self.package_input.split()
            if valores:
                for rec in valores:
                    # Verificar si el paquete está en las líneas de secado_recepcion_ids
                    encontrado = False
                    for line in self.secado_recepcion_ids:
                        if rec == line.package_id.name:
                            encontrado = True
                            break  # Salir del bucle si el paquete es encontrado
                    # Si no se encuentra el paquete, lanzar un ValidationError
                    if not encontrado:
                        raise ValidationError(f"El paquete '{rec}' no está presente en las líneas de recepción.")
                
    def compute_packages_recep(self):
        valores = self.package_input.split()
        if valores:
            for rec in valores:
                # Verificar si el paquete está en las líneas de secado_recepcion_ids
                encontrado = False
                for line in self.secado_recepcion_ids:
                    if rec == line.package_id.name:
                        line.recepcionado = True
                        encontrado = True
                        break  # Salir del bucle si el paquete es encontrado
                
                # Si no se encuentra el paquete, lanzar un ValidationError
                if not encontrado:
                    raise ValidationError(f"El paquete '{rec}' no está presente en las líneas de recepción.")
    
    
    def create_stock_picking(self):
        picking_type = self.picking_type_id
        valores = self.package_input.split()
        location = self.env['stock.location'].search([('produccion_secado_externo', '=', True)], limit=1)

        picking_vals = {
            'partner_id': self.partner_id.id,
            'location_id': location.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'picking_type_id': picking_type.id,
            'origin': self.name,
            'folio_produccion': self.doc_origin,
            'chofer': self.chofer,  # Ubicación de destino
            'rut_chofer': self.chofer_rut,  # Ubicación de destino
            'patente_camion': self.patente_camion,  # Ubicación de destino
            'patente_carro': self.patente_carro,  # Ubicación de destino
            'precio_flete': self.flete,  # Ubicación de destino
            'package_level_ids_details': [],
        }

        package_levels = []
        move_lines = []
        for package in valores:
            secado_paquete = self.env['secado_externo.secado_paquetes'].search([('package_id.name', '=', package)], limit=1)
            
            if not secado_paquete:
                raise ValidationError(f"El paquete '{package}' no está presente en las líneas de recepción.")
            
            if secado_paquete.recepcionado:
                raise ValidationError(f"El paquete '{package}' ya fue recepcionado.")
            
            # Procesar el paquete
            package = secado_paquete.package_id
            if package:
                current_quant_ids = package.quant_ids
                move_vals = {
                    'product_id': current_quant_ids.product_id.id,
                    'name': current_quant_ids.product_id.name,
                    'product_uom_qty': current_quant_ids.quantity,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'location_id': location.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                }
                move_lines.append((0, 0, move_vals))
                
                package_level_vals = {
                    'package_id': package.id,
                    'company_id': self.env.company.id,
                    'location_id': location.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    'picking_id': self.picking_id.id,
                    'is_done': True,
                }
                package_levels.append((0, 0, package_level_vals))
                self.quantity_recep += current_quant_ids.quantity
                self.package_count_recep += 1
                secado_paquete.recepcionado = True
        picking_vals['move_lines'] = move_lines
        picking_vals['package_level_ids_details'] = package_levels

        # Crear el picking
        picking = self.env['stock.picking'].create(picking_vals)
        
        # Confirmar el picking
        picking.action_confirm()
        picking.button_validate()
        
        # Marcar los paquetes como recepcionados
        self.package_input = ''
        self.chofer = ''
        self.chofer_rut = ''
        self.patente_camion = ''
        self.patente_carro = ''
        self.flete = ''
        self.doc_origin = ''
        if self.quantity_recep == self.quantity:
            self.state_recep = 'done'
        else:
            self.state_recep = 'rp'
        self.picking_id = picking.id

        return picking
