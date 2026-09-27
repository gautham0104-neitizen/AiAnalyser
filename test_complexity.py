from backend.analyzer.complexity import ComplexityAnalyzer


code = """
def find_max(arr):
    maximum = arr[0]

    for x in arr:
        if x > maximum:
            maximum = x

    return maximum
"""


analyzer = ComplexityAnalyzer()

result = analyzer.analyze(code)

print(result)