# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import fields, models
import logging
import random

_logger = logging.getLogger(__name__)


class survey_question(models.Model):
    _inherit = 'survey.question'

    conditional = fields.Boolean(
        'Conditional Question',
        copy=False,
        # we add copy = false to avoid wrong link on survey copy,
        # should be improoved
    )
    question_conditional_id = fields.Many2one(
        'survey.question',
        'Question',
        copy=False,
        help="In order to edit this field you should first save the question"
    )
    random_show = fields.Boolean(
        'Random Show',
        copy=False,
        # we add copy = false to avoid wrong link on survey copy,
        # should be improoved
    )
    answer_id = fields.Many2one(
        'survey.label',
        'Answer',
        copy=False,
    )

    _defaults = {
        'random_show': False,
    }

    def validate_question(
            self, cr, uid, question, post, answer_tag, context=None):
        ''' Validate question, depending on question type and parameters '''

        try:
            checker = getattr(self, 'validate_' + question.type)
        except AttributeError:
            _logger.warning(
                question.type + ": This type of question has no validation method")
            return {}
        else:
            # TODO deberiamos emprolijar esto
            if not question.question_conditional_id:
                return checker(cr, uid, question, post, answer_tag, context=context)
            input_answer_id = self.pool['survey.user_input_line'].search(
                cr, uid,
                [('user_input_id.token', '=', post.get('token')),
                 ('question_id', '=', question.question_conditional_id.id)])
            for answers in self.pool['survey.user_input_line'].browse(cr, uid,input_answer_id):
                value_suggested = answers.value_suggested
                if question.conditional and question.answer_id != value_suggested:
                    return {}
                else:
                    return checker(cr, uid, question, post, answer_tag, context=context)
                
    def get_random_label(self, cr, uid, ids, label=False, context=None):
        question = self.browse(cr, uid, ids, context=context)
        labels_ids = label and question.labels_ids_2 or question.labels_ids
        if not question.random_show:
            return labels_ids 
        if not labels_ids:
            return labels_ids
        return random.sample(labels_ids, len(labels_ids))
        

class survey_user_input(models.Model):
    _inherit = 'survey.user_input'

    def get_list_questions(self, cr, uid, survey, user_input_id):

        questions_to_hide = []
        obj_questions = self.pool['survey.question']
        question_ids = obj_questions.search(
            cr,
            uid,
            [('survey_id', '=', survey.id),('conditional', '=', True)])
        for question in obj_questions.browse(cr, uid, question_ids):
            if question.question_conditional_id:
                for answers in question.question_conditional_id.user_input_line_ids:
                    if answers.user_input_id.id == user_input_id:
                        value_suggested = answers.value_suggested
                        if question.answer_id != value_suggested:
                            questions_to_hide.append(question.id)
                            # Init answer
                            for answers1 in question.user_input_line_ids:
                                answers1.value_suggested = None
        return questions_to_hide


