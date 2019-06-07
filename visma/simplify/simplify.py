"""
Initial Author: Siddharth Kothiyal (sidkothiyal, https://github.com/sidkothiyal)
Other Authors:
Owner: AerospaceResearch.net
About: This module aims to create a sort of middleware module to call other modules which can handle/solve different types of equations and expressions.
This module is also responsible for performing tasks like simplification of equations/expressions, and individual functions like, addition, subtraction, multiplication and division in an equation/expression.
Communicates with polynomial roots module, to check if roots of the equation can be found.
Note: Please try to maintain proper documentation
Logic Description:
"""

import copy
from visma.functions.constant import Constant, Zero
from visma.functions.variable import Variable
from visma.functions.operator import Binary
from visma.io.checks import isEquation, getLevelVariables, getOperationsEquation, getOperationsExpression, postSimplification
from visma.io.parser import tokensToString
from visma.io.tokenize import tokenizer
from visma.simplify.addsub import addition, additionEquation, subtraction, subtractionEquation
from visma.simplify.muldiv import multiplication, multiplicationEquation, division, divisionEquation
from visma.functions.structure import Expression


def moveRTokensToLTokens(lTokens, rTokens):
    """Moves tokens in RHS to LHS

    Arguments:
        ltokens {list} -- LHS tokens list
        rtokens {list} -- RHS tokens list

    Returns:
        ltokens {list} -- LHS tokens list
        rtokens {list} -- RHS tokens list
    """
    if len(lTokens) == 0 and len(rTokens) > 0:
        return rTokens, lTokens
    elif isEquation(lTokens, rTokens):
        return lTokens, rTokens
    elif len(lTokens) != 0:
        for i, token in enumerate(rTokens):
            if i == 0 and not isinstance(token, Binary):
                binary = Binary()
                binary.value = '-'
                binary.scope = copy.copy(token.scope)
                binary.scope[-1] -= 1
                lTokens.append(binary)
            if isinstance(token, Binary):
                if token.value in ['+', '-']:
                    if token.value == '-':
                        token.value = '+'
                    else:
                        token.value = '-'
            elif isinstance(token, Constant):
                if token.value < 0:
                    if isinstance(lTokens[-1], Binary):
                        if lTokens[-1].value == '-':
                            token.value *= -1
                            lTokens[-1].value = '+'
                        elif lTokens[-1].value == '+':
                            token.value *= -1
                            lTokens[-1].value = '-'
            elif isinstance(token, Variable):
                if token.coefficient < 0:
                    if isinstance(lTokens[-1], Binary):
                        if lTokens[-1].value == '-':
                            token.coefficient *= -1
                            lTokens[-1].value = '+'
                        elif lTokens[-1].value == '+':
                            token.coefficient *= -1
                            lTokens[-1].value = '-'
            lTokens.append(token)
    rTokens = []
    return lTokens, rTokens


def simplifyEquation(lToks, rToks):
    """Simplifies given equation tokens

    Arguments:
        lToks {list} -- LHS tokens list
        rToks {list} -- RHS tokens list

    Returns:
        lTokens {list} -- LHS tokens list
        rTokens {list} -- RHS tokens list
        availableOperations {list} -- list of operations
        token_string {string} -- simplified result in string
        animation {list} -- list of equation simplification progress
        comments {list} -- list of solution steps
    """
    lTokens = copy.deepcopy(lToks)
    rTokens = copy.deepcopy(rToks)
    animation = []
    comments = [[]]
    lVariables = []
    lVariables.extend(getLevelVariables(lTokens))
    rVariables = []
    rVariables.extend(getLevelVariables(rTokens))
    animBuilder = lToks
    lenToks = len(lToks)
    equalTo = Binary()
    equalTo.scope = [lenToks]
    equalTo.value = '='
    animBuilder.append(equalTo)
    if len(rToks) == 0:
        zero = Zero()
        zero.scope = [lenToks + 1]
        animBuilder.append(zero)
    else:
        animBuilder.extend(rToks)
    animation.append(copy.deepcopy(animBuilder))
    availableOperations = getOperationsEquation(
        lVariables, lTokens, rVariables, rTokens)
    while len(availableOperations) > 0:
        if '/' in availableOperations:
            lTokens, rTokens, availableOperations, token_string, anim, com = divisionEquation(
                lTokens, rTokens)
            animation.pop(len(animation) - 1)
            animation.extend(anim)
            comments.extend(com)
        elif '*' in availableOperations:
            lTokens, rTokens, availableOperations, token_string, anim, com = multiplicationEquation(
                lTokens, rTokens)
            animation.pop(len(animation) - 1)
            animation.extend(anim)
            comments.extend(com)
        elif '+' in availableOperations:
            lTokens, rTokens, availableOperations, token_string, anim, com = additionEquation(
                lTokens, rTokens)
            animation.pop(len(animation) - 1)
            animation.extend(anim)
            comments.extend(com)
        elif '-' in availableOperations:
            lTokens, rTokens, availableOperations, token_string, anim, com = subtractionEquation(
                lTokens, rTokens)
            animation.pop(len(animation) - 1)
            animation.extend(anim)
            comments.extend(com)

        lVariables = getLevelVariables(lTokens)
        rVariables = getLevelVariables(rTokens)
        availableOperations = getOperationsEquation(
            lVariables, lTokens, rVariables, rTokens)

    moved = False
    if len(rTokens) > 0:
        moved = True
        lTokens, rTokens = moveRTokensToLTokens(lTokens, rTokens)
    tokenToStringBuilder = copy.deepcopy(lTokens)
    lenToks = len(lTokens)
    equalTo = Binary()
    equalTo.scope = [lenToks]
    equalTo.value = '='
    tokenToStringBuilder.append(equalTo)
    if len(rTokens) == 0:
        zero = Zero()
        zero.scope = [lenToks + 1]
        tokenToStringBuilder.append(zero)
    else:
        tokenToStringBuilder.extend(rTokens)
    if moved:
        animation.append(copy.deepcopy(tokenToStringBuilder))
        comments.append(['Moving the rest of variables/constants to LHS'])

    token_string = tokensToString(tokenToStringBuilder)
    return lTokens, rTokens, availableOperations, token_string, animation, comments


def simplify(tokens):
    tokens_orig = copy.deepcopy(tokens)
    animation = [tokens_orig]
    comments = [[]]
    tokens, anim1, comment1 = expressionSimplification(tokens_orig)
    animation.extend(anim1)
    comments.extend(comment1)
    tokens, availableOperations, token_string, anim2, comment2 = simplifyNormal(tokens)
    anim2.pop(0)
    animation.extend(anim2)
    comments.extend(comment2)
    return tokens, availableOperations, token_string, animation, comments


def expressionSimplification(tokens1):
    animation = []
    comments = []
    simToks = []

    # TODO: add comments & animations.
    # TODO: It would fail if more than 50 consecutive expressions are multiplied, make use of flag "mlpre"
    # while(mlpre):
    mlpre = True
    for _ in range(50):
        if not mlpre:
            break
        for i, _ in enumerate(tokens1):
            mlpre = False
            if isinstance(tokens1[i], Expression):
                if (i > 1):
                    if (tokens1[i - 1].value == '*'):
                        tokens1[i].tokens, _, _ = expressionSimplification(tokens1[i].tokens)
                        # animation.extend(anim1)
                        # comments.extend(comment1)
                        tokens1[i].tokens, _, _, _, _ = simplifyNormal(tokens1[i].tokens)
                        # anim2.pop(0)
                        # animation.extend(anim2)
                        # comments.extend(comment2)

                        if isinstance(tokens1[i - 2], Expression):
                            tokens1[i - 2].tokens, _, _ = expressionSimplification(tokens1[i - 2].tokens)
                            # animation.extend(anim1)
                            # comments.extend(comment1)
                            tokens1[i - 2].tokens, _, _, _, _ = simplifyNormal(tokens1[i - 2].tokens)
                            # anim2.pop(0)
                            # animation.extend(anim2)
                            # comments.extend(comment2)

                        mlpre = True
                        a = tokens1[i - 2]
                        b = tokens1[i]
                        c = a * b
                        if isinstance(c, Expression):
                            c.tokens, _, _ = expressionSimplification(c.tokens)
                            # animation.extend(anim3)
                            # comments.extend(comment3)
                            c.tokens, _, _, _, _ = simplifyNormal(c.tokens)
                            # animation.extend(anim4)
                            # comments.extend(comment4)
                        tokens1[i] = c
                        del tokens1[i - 1]
                        del tokens1[i - 2]
                        animation.append(tokens1)
                        break

    for i, _ in enumerate(tokens1):
        if isinstance(tokens1[i], Expression):
            newToks, anim5, comment5 = expressionSimplification(tokens1[i].tokens)
            animation.extend(anim5)
            comments.extend(comment5)
            newToks, _, _, anim6, comment6 = simplifyNormal(newToks)
            anim6.pop(0)
            animation.extend(anim6)
            comments.extend(comment6)
            if not simToks:
                simToks.extend(newToks)
            elif (simToks[len(simToks) - 1].value == '+'):
                if isinstance(newToks[0], Constant):
                    if (newToks[0].value < 0):
                        simToks.pop()
                simToks.extend(newToks)
            elif (simToks[len(simToks) - 1].value == '-'):
                for _, x in enumerate(newToks):
                    if x.value == '+':
                        x.value = '-'
                    elif x.value == '-':
                        x.value = '+'
                if (isinstance(newToks[0], Constant)):
                    if (newToks[0].value < 0):
                        simToks[-1].value = '+'
                        newToks[0].value = abs(newToks[0].value)
                elif (isinstance(newToks[0], Variable)):
                    if (newToks[0].coefficient < 0):
                        simToks[-1].value = '+'
                        newToks[0].coefficient = abs(newToks[0].coefficient)
                simToks.extend(newToks)
        else:
            simToks.extend([tokens1[i]])
    return tokenizer(tokensToString(simToks)), animation, comments


def simplifyNormal(tokens):
    """Simplifies given expression tokens

    Arguments:
        tokens {list} -- tokens list

    Returns:
        tokens {list} -- tokens list
        availableOperations {list} -- list of operations
        token_string {string} -- simplified result in string
        animation {list} -- list of equation simplification progress
        comments {list} -- list of solution steps
    """
    tokens_orig = copy.deepcopy(tokens)
    animation = [tokens_orig]
    variables = []
    comments = []
    variables.extend(getLevelVariables(tokens))
    availableOperations = getOperationsExpression(variables, tokens)
    while len(availableOperations) > 0:
        if '/' in availableOperations:
            tokens_temp = copy.deepcopy(tokens)
            tokens, availableOperations, token_string, anim, com = division(
                tokens_temp)
            animation.pop(len(animation) - 1)
            animation.extend(anim)
            comments.extend(com)
        elif '*' in availableOperations:
            tokens_temp = copy.deepcopy(tokens)
            tokens, availableOperations, token_string, anim, com = multiplication(
                tokens_temp)
            animation.pop(len(animation) - 1)
            animation.extend(anim)
            comments.extend(com)
        elif '+' in availableOperations:
            tokens_temp = copy.deepcopy(tokens)
            tokens, availableOperations, token_string, anim, com = addition(
                tokens_temp)
            animation.pop(len(animation) - 1)
            animation.extend(anim)
            comments.extend(com)
        elif '-' in availableOperations:
            tokens_temp = copy.deepcopy(tokens)
            tokens, availableOperations, token_string, anim, com = subtraction(
                tokens_temp)
            animation.pop(len(animation) - 1)
            animation.extend(anim)
            comments.extend(com)
    tokens, animation = postSimplification(tokens, animation)
    token_string = tokensToString(tokens)
    return tokens, availableOperations, token_string, animation, comments


'''
def defineScopeVariable(variable, scope):
    token = copy.deepcopy(variable)
    local_scope = copy.deepcopy(scope)
    if isinstance(token.value, list):
        for j, val in enumerate(token.value):
            if val.__class__ in [Binary, Variable, Constant, Expression]:
                local_scope_value = copy.deepcopy(local_scope)
                local_scope_value.extend(-1)
                local_scope_value.extend(j)
                val.scope = local_scope_value

    if isinstance(token.power, list):
        for j, val in enumerate(token.value):
            if val.__class__ in [Binary, Variable, Constant, Expression]:
                local_scope_value = copy.deepcopy(local_scope)
                local_scope_value.extend(-2)
                local_scope_value.extend(j)
                val.scope = local_scope_value

    return token


def defineScopeConstant(constant, scope):
    token = copy.deepcopy(constant)
    local_scope = copy.deepcopy(scope)
    if isinstance(token.value, list):
        for j, val in enumerate(token.value):
            if val.__class__ in [Binary, Variable, Constant, Expression]:
                local_scope_value = copy.deepcopy(local_scope)
                local_scope_value.extend(-1)
                local_scope_value.extend(j)
                val.scope = local_scope_value

    if isinstance(token.power, list):
        for j, val in enumerate(token.value):
            if val.__class__ in [Binary, Variable, Constant, Expression]:
                local_scope_value = copy.deepcopy(local_scope)
                local_scope_value.extend(-2)
                local_scope_value.extend(j)
                val.scope = local_scope_value
    return token


def defineScope(tokens, scope=None):
    if scope is None:
        scope = []
    i = 0
    for token in tokens:
        local_scope = copy.deepcopy(scope)
        local_scope.extend(i)
        token.scope = local_scope
        if isinstance(token, Variable):
            token = defineScopeVariable(token, copy.deepcopy(local_scope))
        elif isinstance(token, Constant):
            token = defineScopeConstant(token, copy.deepcopy(local_scope))
        elif isinstance(token, Expression):
            token.tokens = defineScope(token.tokens, local_scope)
        elif isinstance(token, Binary):
            pass
        i += 1
    return tokens
'''
