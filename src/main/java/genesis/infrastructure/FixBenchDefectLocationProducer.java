package genesis.infrastructure;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import genesis.corpus.CorpusUtils;
import genesis.node.MyCtNode;
import spoon.reflect.declaration.CtClass;
import spoon.reflect.declaration.CtConstructor;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtPackage;
import spoon.reflect.visitor.filter.TypeFilter;

/**
 * 
 * Produces the localization.log file expected by Genesis.
 * diff ->
 * (diff -> file * line number) ->
 * (file -> Ast) ->
 * (Ast -> line number -> Set[line numbers]) ->
 * Set[line numbers]
 *
 * Requires info -> file
 */
public class FixBenchDefectLocationProducer {
	
	final static String pathToPtbench = "/home/root/Workspace/PTBench-Data/";
	final static String pathToCheckout = "/home/root/Workspace/bowen_bench_checkouts/";
	
	public static String infoToRepoPath(String infoPath) throws FileNotFoundException, IOException {
		String repoName = null;
		try (BufferedReader br = new BufferedReader(new FileReader(infoPath))) {
			String strLine;

			while ((strLine = br.readLine()) != null)   {
				
				if (strLine.startsWith("repoName")) {
					repoName = strLine.split("repoName:")[1];
					repoName = repoName.replace("#", "/");
					break;
				}
			}
		}
		if (repoName == null) throw new RuntimeException("shit");
		
		String path = pathToCheckout + repoName.split("/")[1];
		
		
		return path;
	}
	
	public static List<String> readDiff(String filePath) throws IOException {
		List<String> linesInDiff = new ArrayList<>();
		try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
			String strLine;

			while ((strLine = br.readLine()) != null)   {
				
				linesInDiff.add(strLine);
			}
		}
		
		return linesInDiff;
	}
	
	public static List<Integer> diffToLineNumbers(List<String> linesInDiff) {
		List<Integer> results = new ArrayList<>();
		for (String line : linesInDiff) {
			if (!line.contains("@@")) continue;
			String[] splitted = line.split("@@")[1].split(" ");
			
			for (String token : splitted) {
				if (token.contains("-")) {
					int number = Integer.parseInt(token.substring(1).split(",")[0]);
					results.add(number);
				}
			}
		}
		return results;
	}
	
	public static String diffToFile(List<String> linesInDiff) {
		for (String line : linesInDiff) {
			if (!line.contains("--- a")) {
				continue;
			}
			
			return line.split("--- a")[1];
		}
		throw new RuntimeException("oh shit");
	}
	
	public  static CtPackage fileToAst(String repoPath, String filePath) {

		System.out.println("repoPath=" + repoPath);
		if (!repoPath.endsWith("/")) {
			repoPath += "/";
		}
		
		TestAppManager parser = new TestAppManager(repoPath);
		MyCtNode n = parser.getCtNode(repoPath + filePath, true);
		
		if (n == null) {
			throw new RuntimeException("cannot handle!");
		}
		
		CtPackage ast = ((CtPackage)n.getRawObject());
		return ast;
	}
	
	public static List<Integer> astAndLineNumberToAllLineNumbers(CtPackage ast, List<Integer> lineNumbers) {
		for (Integer lineNumber : lineNumbers) {
			List<Integer> result = astAndLineNumberToAllLineNumbersInMethod(ast, lineNumber);
			if (result != null) {
				return result;
			}
		}
		
		System.out.println("Can't find it in a method. Using all lines in class instead. This makes sense for things like adding fields");
		
		
		
		for (Integer lineNumber : lineNumbers) {
			List<Integer> result = astAndLineNumberToAllLineNumbersInClass(ast, lineNumber);
			if (result != null) {
				return result;
			}
		}
		
		throw new RuntimeException("cannot find right line numbers");
	}
	
	public static List<Integer> astAndLineNumberToAllLineNumbersInMethod(CtPackage ast, int lineNumber) {
		
		Set<CtMethod> methodsContainingLine = new HashSet<>();
		Set<CtConstructor> ctorsContainingLine = new HashSet<>();
		
		List<CtMethod> elements = ast.getElements(new TypeFilter<>(CtMethod.class));
		for (CtMethod method : elements) {
			
			int start = method.getPosition().getLine();
			
			if (method.getBody() == null) {
				// perhaps an abstract method. Just skip
				continue;
				
			}
			int end = method.getBody().getPosition().getEndLine();
			
			System.out.println("\tMethod: " + method.getSignature() + " start=" + start + ", end=" + end);
			System.out.println("\tline number=" + lineNumber);
			
			if (start <= lineNumber && end >= lineNumber) {
				System.out.println("\t\tFOUND");
				methodsContainingLine.add(method);
			}
		}
		
		List<CtConstructor> ctorElements = ast.getElements(new TypeFilter<>(CtConstructor.class));
		for (CtConstructor ctorElement : ctorElements) {
			
			int start = ctorElement.getPosition().getLine();
			
			if (ctorElement.getBody() == null) {
				// perhaps an abstract method. Just skip
				continue;
				
			}
			int end = start + ctorElement.getBody().toString().split("\n").length;
			
			System.out.println("\tMethod (ctor): " + ctorElement.getSignature() + " start=" + start + ", end=" + end);
			System.out.println("\tline number=" + lineNumber);
			
			if (start <= lineNumber && end >= lineNumber) {
				ctorsContainingLine.add(ctorElement);
			}
		}
		
		if (methodsContainingLine.isEmpty() && ctorsContainingLine.isEmpty()) {
			return null;
		}
		List<Integer> result = new ArrayList<>();
		for (CtMethod methodContainingLine : methodsContainingLine) {
			int start = methodContainingLine.getPosition().getLine();
			int end = methodContainingLine.getBody().getPosition().getEndLine();
			
			for (int i = start; i <= end; i++) {
				result.add(i);
			}
		}
		for (CtConstructor ctorContainingLine : ctorsContainingLine) {
			int start = ctorContainingLine.getPosition().getLine();
			int end = start + ctorContainingLine.getBody().toString().split("\n").length;
			
			for (int i = start; i <= end; i++) {
				result.add(i);
			}
		}
		
		return result;
	}
	
	public static List<Integer> astAndLineNumberToAllLineNumbersInClass(CtPackage ast, int lineNumber) {
		List<CtClass> clazzs = ast.getElements(new TypeFilter<>(CtClass.class));
		
		Set<CtClass> clazzsContainingLine = new HashSet<>();
		for (CtClass clazz : clazzs) {
			int start = clazz.getPosition().getLine();
			int end = clazz.getPosition().getSourceEnd();
			
			List<CtMethod> methodsInClass = clazz.getElements(new TypeFilter<>(CtMethod.class));
			for (CtMethod method : methodsInClass) {
				if (method.getBody() == null) {
					end = method.getPosition().getLine();
					continue;
				}
				int lastLine = method.getBody().getPosition().getEndLine();
				if (lastLine > end) {
					end = lastLine;
				}
			}
			
			System.out.println("\tClass: " + clazz.getSignature() + " start=" + start + ", end=" + end);
			System.out.println("\tline number=" + lineNumber);
			
			if (start <= lineNumber && end >= lineNumber) {
				clazzsContainingLine.add(clazz);
				break;
			}
		}
		
		if (clazzsContainingLine.isEmpty()) {
			return null;
		}
		List<Integer> result = new ArrayList<>();
		for (CtClass clazzContainingLine  : clazzsContainingLine) {
			int start = clazzContainingLine.getPosition().getLine();
			int end = clazzContainingLine.getPosition().getEndLine();
			
			
			for (int i = start; i <= end; i++) {
				result.add(i);
			}
		}
		
		return result;
	}
	
	
	public static void writeLocalizationFile(String filenameToWriteTo, String filePath, 
			List<Integer> lineNumbers, List<Integer> diffLineNumbers) throws IOException {
		
		int lengthToReport = 0;
		

		int biggestDiffLineNumber = 0;
		for (Integer lineNumber : diffLineNumbers) {
			if (lineNumber > biggestDiffLineNumber) biggestDiffLineNumber = lineNumber;
		}
		for (Integer lineNumber : lineNumbers) {
			if (diffLineNumbers.contains(lineNumber)) {
				continue;
			}
			if (lineNumber > biggestDiffLineNumber) {
				continue;
			}
		
			lengthToReport ++;
		}
		
		
		try (BufferedWriter writer = new BufferedWriter(new FileWriter(filenameToWriteTo))) {
			writer.write(lengthToReport + "\n");
			
			for (Integer lineNumber : diffLineNumbers) {
				String line = filePath + " " + lineNumber + " -1 0.99";
				writer.write(line + "\n");
				
				if (lineNumber > biggestDiffLineNumber) biggestDiffLineNumber = lineNumber;
			}
			
			for (Integer lineNumber : lineNumbers) {
				if (diffLineNumbers.contains(lineNumber)) {
					continue;
				}
				if (lineNumber > biggestDiffLineNumber) {
					continue;
				}
				
				String line = filePath + " " + lineNumber + " -1 0.95";
				writer.write(line + "\n");
				
			}

		}
	}
	
	
	public static void main(String... args) throws Exception {
		
		System.out.println("start");
		String pathToInfo = args[0];
		String pathToDiff = args[1];
		
		if (args.length == 2) {
			writeAllLinesInTouchedMethod(pathToInfo, pathToDiff, null);
		} else {
			String pathToRepo = args[2];
			writeAllLinesInTouchedMethod(pathToInfo, pathToDiff, pathToRepo);
		}
		System.out.println("end");
	}

	/**
	 * Given the path to the .info file, and the path to the diff,
	 * returns all the line numbers in the method that was touched in the diff.
	 * 
	 * This assumes only one method was touched. 
	 * Thus, it picks up the line number of the first hunk that was changed and uses it to find the line numbers of the method
	 * 
	 * @param pathToInfo
	 * @param pathToDiff
	 * @throws FileNotFoundException
	 * @throws IOException
	 */
	public static void writeAllLinesInTouchedMethod(String pathToInfo, String pathToDiff, String pathToRepo)
			throws FileNotFoundException, IOException {
		if (pathToRepo == null) {
			pathToRepo = infoToRepoPath(pathToInfo); // info -> repo
		}
		List<String> diff = readDiff(pathToDiff); // diff
		List<Integer> diffLineNumber = diffToLineNumbers(diff); //diff -> set<line number>
		String filePath = diffToFile(diff);  // diff -> file
		
		CtPackage ast = fileToAst(pathToRepo, filePath); // file -> ast
		
		List<Integer> lineNumbers = astAndLineNumberToAllLineNumbers(ast, diffLineNumber); // ast -> set<line number> -> list<line numbers>
		
		writeLocalizationFile("localization.log", filePath, lineNumbers, diffLineNumber);
	}

}
