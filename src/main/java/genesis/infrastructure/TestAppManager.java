package genesis.infrastructure;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Scanner;

import genesis.Config;
import genesis.GenesisException;
import genesis.corpus.CorpusUtils;
import genesis.node.MyCtNode;
import genesis.repair.ASTNodeFetcher.LocationScanner;
import genesis.repair.validation.Testcase;
import spoon.Launcher;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.declaration.CtPackage;
import spoon.reflect.factory.Factory;
import spoon.reflect.visitor.CtScanner;

/**
 * 
 * Use this to build the serialized ASTs from the code.
 * Run like the following:
 * MAVEN_OPTS="-Xms256m -Xmx16g" mvn exec:java -Dexec.mainClass="genesis.infrastructure.TestAppManager" -Dexec.args="/home/root/Workspace/bowen_bench_checkouts/flinkStreamSQL/ /home/root/Workspace/bowen_bench_checkouts/flinkStreamSQL/mysql/mysql-sink/src/main/java/com/dtstack/flink/sql/sink/mysql/DBSink.java /home/root/Workspace/github/data/__DTStack_flinkStreamSQL_po/fixed_154cf4cd8d3e25a679ed085009d8aae06f775162.po" &> test.log
 * args[0] is the path to the project repo, args[1] is the file we want to build an AST of, and args[2] is where the output should go.
 * 
 * This differs from AppManager by using Spoon's noclasspath mode. 
 * We find that many examples on GitHub can only be compiled using noclasspath mode.
 * fixbench_create_asts.py is the python script that runs this file.
 */
public class TestAppManager {

	File srcdir;
	BuildEngineKind engineKind;
	String engineScript;
	Launcher l;

	class CompileSession {
		HashSet<String> sourcepath;
		String classpath;
		HashMap<String, String> fullargs;

		public CompileSession(String line) {
			ArrayList<String> tmp = new ArrayList<String>();
			String curStr = "";
			for (int i = 0; i < line.length(); i++) {
				if (line.charAt(i) == '-' && (i == 0 || line.charAt(i - 1) == ' ')) {
					if (!curStr.trim().equals(""))
						tmp.add(curStr.trim());
					curStr = "";
				}
				curStr += line.charAt(i);
			}
			// System.out.println(line);
			if (!curStr.trim().equals(""))
				tmp.add(curStr);
			fullargs = new HashMap<String, String>();
			for (String s : tmp) {
				int idx = s.indexOf(' ');
				if (idx == -1)
					fullargs.put(s, "");
				else {
					String s1 = s.substring(0, idx).trim();
					String s2 = s.substring(idx + 1).trim();
					fullargs.put(s1, s2);
					if (s1.equals("-sourcepath")) {
						String[] tokens = s2.trim().split(":");
						sourcepath = new HashSet<String>();
						for (String token : tokens) {
							if (!token.equals(""))
								sourcepath.add(token);
						}
						/*
						 * sourcepath = s2; if (sourcepath.endsWith(":")) sourcepath =
						 * sourcepath.substring(0, sourcepath.length() - 1);
						 */
					}
					if (s1.equals("-classpath"))
						classpath = s2;
				}
			}
			// System.out.println(fullargs);
		}
	}

	ArrayList<CompileSession> compSessions;

	class TestSession {
		HashSet<String> testClasses;
		String classpath;
		String sourcepath;
	}

	ArrayList<TestSession> testSessions;

	public TestAppManager(String srcdir) {
		this.srcdir = new File(srcdir);
		this.l = null;
		if (this.srcdir == null || (!this.srcdir.isDirectory()))
			throw new GenesisException("Expect a src direcotry for AppParser!");
		this.engineKind = determineBuildEngine(this.srcdir);
		this.engineScript = getEngineScript(engineKind);
		this.compSessions = null;
		this.testSessions = null;
	}

	public TestAppManager(File srcdir) {
		this.srcdir = srcdir;
		this.l = null;
		if (this.srcdir == null || (!this.srcdir.isDirectory()))
			throw new GenesisException("Expect a src direcotry for AppParser!");
		this.engineKind = determineBuildEngine(this.srcdir);
		this.engineScript = getEngineScript(engineKind);
		this.compSessions = null;
	}

	private String getEngineScript(BuildEngineKind k) {
		if (k == null)
			return null;
		String scriptURL = null;
		switch (k) {
		case ANT:
			scriptURL = Config.pythonSourceDir + "/ant.py";
		case MAVEN:
			scriptURL = Config.pythonSourceDir + "/maven.py";
		}
		return "python2 " + Paths.get(scriptURL).toAbsolutePath().toString();
	}

	private BuildEngineKind determineBuildEngine(File srcdir) {
		boolean foundPomXml = false;
		boolean foundBuildXml = false;
		File[] files = srcdir.listFiles();
		for (File f : files) {
			String fname = f.getName();
			if (fname.equals("build.xml"))
				foundBuildXml = true;
			if (fname.equals("pom.xml"))
				foundPomXml = true;
		}
		if (foundPomXml)
			return BuildEngineKind.MAVEN;
		if (foundBuildXml)
			return BuildEngineKind.ANT;
		return null;
	}

	public BuildEngineKind getBuildEngineKind() {
		return engineKind;
	}

	public boolean clean() {
		assert (engineKind != null);
		String cmd = engineScript + " --clean " + this.srcdir.getAbsolutePath();
		int ret = ExecShellCmd.runCmd(cmd);
		return ret == 0;
	}

	public boolean compile(boolean clean) {
		assert (engineKind != null);
		String cmd = engineScript + " --compile ";
		if (clean)
			cmd += "--clean ";
		cmd += this.srcdir.getAbsolutePath();
		int ret = ExecShellCmd.runCmd(cmd);
		return ret == 0;
	}

	public void initializeCompileSessionsWithFile(String argFname) {
//		rewriteClassPathForBukkit(argFname);

		List<String> lines = null;
		try {
			lines = Files.readAllLines(Paths.get(argFname));
		} catch (IOException e) {
			throw new GenesisException("Unable to read argument log file " + argFname);
		}

		compSessions = new ArrayList<CompileSession>();
		for (String line : lines) {
			// System.out.println("OUT line: " + line);
			compSessions.add(new CompileSession(line));
		}
	}

	public boolean initializeCompileSessions(String argFname, boolean verbose) {
//		rewriteClassPathForBukkit(argFname);

		String cmd = engineScript + " --getargs=" + argFname + " " + srcdir.getAbsolutePath() + " > /tmp/log"
				+ Integer.toString(srcdir.getAbsolutePath().hashCode()) + " 2>&1";
		// System.out.println("cmd exec: " + cmd);
		int ret = ExecShellCmd.runCmd(cmd);
		if (ret != 0) {
			if (verbose) {
				System.out.println("Cmd faild: " + cmd);
				System.out.println("Unable to compile the application!");
			}
			return false;
		}

		initializeCompileSessionsWithFile(argFname);
		return true;
	}

	public static void rewriteClassPathForBukkit(String argFname) {
		// add custom args for classpath

		try {
			List<String> lines = Files.readAllLines(Paths.get(argFname));

			new File(argFname).delete();
			try (BufferedWriter writer = new BufferedWriter(new FileWriter(argFname))) {
				for (String line : lines) {
					String replacement = line.replace(" -sourcepath",
							"/root/.m2/repository/org/bukkit/bukkit/1.12.2-R0.1-SNAPSHOT/bukkit-1.12.2-R0.1-SNAPSHOT.jar:/root/.m2/repository/net/md-5/bungeecord-chat/1.12-SNAPSHOT/bungeecord-chat-1.12-SNAPSHOT.jar: -sourcepath");
					writer.write(replacement);
					writer.newLine();

//					System.out.println("rewriting  : " + replacement);
				}

			} catch (Exception e) {
				e.printStackTrace();
				System.err.println("rewrite failed");
			}
		} catch (IOException e1) {
			e1.printStackTrace();
		}
	}

	public void initializeTestSessionsWithFile(String testinfoFname) {
		List<String> lines = null;
		try {
			lines = Files.readAllLines(Paths.get(testinfoFname));
		} catch (IOException e) {
			throw new GenesisException("Unable to read temporary testinfo file " + testinfoFname);
		}

		// for (String line : lines)
		// System.out.println("OUT line: " + line);

		int pos = 0;
		int m = Integer.parseInt(lines.get(pos).trim());
		pos++;
		testSessions = new ArrayList<TestSession>();
		for (int i = 0; i < m; i++) {
			pos += 4;
			TestSession session = new TestSession();
			session.classpath = lines.get(pos).trim();
			pos++;
			session.sourcepath = lines.get(pos).trim();
			pos++;
			Scanner s = new Scanner(lines.get(pos));
			int n = s.nextInt();
			s.close();
			pos++;
			session.testClasses = new HashSet<String>();
			for (int j = 0; j < n; j++) {
				int u = Integer.parseInt(lines.get(pos).trim());
				pos++;
				for (int k = 0; k < u; k++) {
					s = new Scanner(lines.get(pos));
					pos++;
					String testClass = s.next();
					s.close();
					session.testClasses.add(testClass);
				}
			}
			testSessions.add(session);
		}
	}

	public boolean initializeTestSessions(String testinfoFname, boolean verbose) {
		String cmd = engineScript + " --testinfo=" + testinfoFname + " " + srcdir.getAbsolutePath() + " > /tmp/log"
				+ Integer.toString(srcdir.getAbsolutePath().hashCode()) + " 2>&1";
		// System.out.println("cmd exec: " + cmd);
		int ret = ExecShellCmd.runCmd(cmd);
		if (ret != 0) {
			if (verbose)
				System.out.println("Cmd failed: " + cmd);
			return false;
		}

		initializeTestSessionsWithFile(testinfoFname);

		return true;
	}

	private CompileSession getCompileSession(String srcfile, boolean verbose) {
		assert (engineKind != null);
		if (compSessions == null) {
			boolean ret = initializeCompileSessions(Config.tmpargfile, verbose);
			if (!ret) {
				System.out.println("Cannot fetch the argument list for the project!");
				return null;
			}
		}
		CompileSession theSession = null;
		// System.out.println("target: " +
		// Paths.get(srcfile).toAbsolutePath().toString());

		for (CompileSession se : compSessions) {
//			System.out.println("Checking sourcepath  " + se.sourcepath);
			for (String spath : se.sourcepath) {
//				System.out.println(" checking eq : " + spath);
//				System.out.println("          vs : " + srcfile);
				if (Paths.get(srcfile).toAbsolutePath().startsWith(Paths.get(spath).toAbsolutePath().toString())) {
					theSession = se;
					break;
				}
			}
		}
		return theSession;
	}

	private TestSession getTestSession(String srcfile, boolean verbose) {
		assert (engineKind != null);
		if (testSessions == null) {
			boolean ret = initializeTestSessions(Config.tmpTestinfoFile, verbose);
			if (!ret) {
				System.out.println("Cannot fetch the argument list for the project!");
				return null;
			}
		}
		Path absPath = Paths.get(srcfile).toAbsolutePath();
		for (TestSession se : testSessions) {
			if (absPath.startsWith(Paths.get(se.sourcepath).toAbsolutePath().toString())) {
				return se;
			}
		}
		return null;
	}

	private String guessFile(String filePath, String[] srcPaths) {
		for (String sPath : srcPaths) {
			String fPath = sPath + "/" + filePath;
			if (new File(fPath).isFile()) {
				return fPath;
			}
		}
		// The file doesn't appear to be from this project.
		return null;
	}

	public String guessSrcFile(String packageName, String classFile) {
		return guessSrcFile(packageName.replaceAll("\\.", "/") + "/" + classFile);
	}

	public String guessSrcFile(String filePath) {
		return guessFile(filePath, compSessions.stream().flatMap(e -> e.sourcepath.stream()).toArray(String[]::new));
	}

	public String guessTestFile(String packageName, String classFile) {
		return guessTestFile(packageName.replaceAll("\\.", "/") + "/" + classFile);
	}

	public String guessTestFile(String filePath) {
		return guessFile(filePath, testSessions.stream().map(e -> e.sourcepath).toArray(String[]::new));
	}

	public static MyCtNode spoonCompile(Launcher l, String srcfile, String classpath) {
		String[] spoonargs = { "-i", "", "--output-type", "nooutput", "-o", "/tmp/spooned", "--source-classpath",
				classpath };
		spoonargs[1] = srcfile;
		l.run(spoonargs);
		Factory f = l.getFactory();
		CtPackage p = f.Package().getRootPackage();

		if (p == null) {
			System.out.println("Spoon compilation failed!");
			System.out.println("Args: " + Arrays.asList(spoonargs).toString());
			return null;
		} else
			return new MyCtNode(p, false);
	}
	
	
	public static MyCtNode spoonCompileNoClassPath(Launcher l, String srcfile) {
		String[] spoonargs = { "-i", "", "--output-type", "nooutput", "-o", "/tmp/spooned", "--noclasspath"};
		spoonargs[1] = srcfile;
		l.getEnvironment().setNoClasspath(true);
		l.run(spoonargs);
		Factory f = l.getFactory();
		
		CtPackage p = f.Package().getRootPackage();

		if (p == null) {
			System.out.println("Spoon compilation failed!");
			System.out.println("Args: " + Arrays.asList(spoonargs).toString());
			return null;
		} else
			return new MyCtNode(p, false);
	}

	public MyCtNode getCtNode(String srcfile, boolean verbose) {
		CompileSession theSession = getCompileSession(srcfile, verbose);
		if (theSession == null) {
			if (verbose) {
				System.out.println("Cannot determine the classpath for the file!");
				System.out.println("Target file: " + Paths.get(srcfile).toAbsolutePath().toString());
				if (compSessions != null) {
					for (CompileSession se : compSessions) {
						for (String spath : se.sourcepath)
							System.out.println("Session: " + Paths.get(spath).toAbsolutePath().toString());
					}
				}
			}
			l = new Launcher();
			return spoonCompileNoClassPath(l, srcfile);
		}

		try {
			l = new Launcher();
			return spoonCompile(l, srcfile, theSession.classpath);
		} catch (Exception e) {
			System.out.println("Exception! Cannot spoonCompile. Falling back to noClasspath");
			e.printStackTrace();
			l = new Launcher();
			return spoonCompileNoClassPath(l, srcfile);
			
		}
	}

	public String getClasspath(String srcfile, boolean verbose) {
		CompileSession theSession = getCompileSession(srcfile, verbose);
		return theSession.classpath;
	}

	public String getTestClasspath(String testfile, boolean verbose) {
		return getTestSession(testfile, verbose).classpath;
	}

	public Factory getFactory() {
		if (l == null)
			return null;
		return l.getFactory();
	}

	public static void main(String[] args) {
		if (args.length < 1)
			System.exit(1);
		TestAppManager parser = new TestAppManager(args[0]);
		if (parser.getBuildEngineKind() == null) {
			System.out.println("Unable to detect the build engine. Only support Ant, Maven, and Gradle.");
			System.exit(1);
		}
		boolean succ = true;

		if (args.length < 2)
			succ = parser.compile(true);
		else {
			MyCtNode n = parser.getCtNode(args[1], true);
			succ = (n != null);

//			n.acceptScanner(s);
//			System.out.println("hello");
//			System.out.println(n.codeString());
//			System.out.println(n.getRawObject());
//			System.out.println(n.getRawObject().getClass());
//			System.out.println(n.getChild("packs"));
//			System.out.println(n.getChild("types"));
//			System.out.println(n.getChild("simpleNames"));
//			System.out.println(n.getChild("implicit"));
			boolean writeSucc = false;

			// uncommenting for printing the components of the ast
//			((CtPackage) n.getRawObject()).accept(new CtScanner() {
//
//				@Override
//				public void enter(CtElement ref) {
//					System.out.println(ref);
//				}
//			});

			new File(new File(args[2]).getParent()).mkdirs();
			ObjectOutputStream oos = null;
			try {
				System.out.println("going to write to ..... " + args[2]);

				oos = new ObjectOutputStream(new FileOutputStream(args[2]));
				n.writeToStream(oos);

				oos.close();

				System.out.println("successfully written to ..... " + args[2]);
			} catch (IOException e) {
				e.printStackTrace();
				System.out.println("error while writing ..... " + args[2]);
			} catch (Throwable t) {

				System.out.println("throwable while writing ..... " + args[2]);
			} finally {
				if (oos != null)
					try {
						oos.close();
					} catch (IOException e) {
						System.out.println("error while closing ..... " + args[2]);
						e.printStackTrace();
					}
			}

//			LocationScanner scanner = new LocationScanner(loc);
//			root.acceptScanner(scanner);
			System.out.println("try to read ..... " + args[2]);
			try {
				MyCtNode read = CorpusUtils.parseJavaAST(args[2]);

				writeSucc = read != null;

				if (!writeSucc) {
					System.out.println("Wrote something, but it can't be read (returned null) " + args[2]);
					boolean succDelete = new File(args[2]).delete();
					if (succDelete) {
						System.out.println(
								"\tTried to delete but failed! (this is fine if the file didn't exist) " + args[2]);
					}
					System.exit(1);

				}
			} catch (Throwable e) {
				e.printStackTrace();
				System.out.println("Wrote something, but it can't be read as it threw! " + args[2]);
				boolean succDelete = new File(args[2]).delete();

				if (succDelete) {
					System.out.println("\tTried to delete but failed! " + args[2]);
				}
				System.exit(1);
			}
			System.out.println("Wrote something at " + args[2]);

		}
		if (!succ) {
			System.out.println("Compilation failed at some point!");
			System.exit(1);
		}
	}

	public int getTestSessionId(String testClass) {
		assert (testSessions != null);
		for (int i = 0; i < testSessions.size(); i++) {
			TestSession session = testSessions.get(i);
			if (session.testClasses.contains(testClass))
				return i;
		}
		return -1;
	}

	public String getTestSessionClasspath(Integer id) {
		assert (testSessions != null);
		if (id < 0 || id >= testSessions.size())
			throw new GenesisException(
					"Invalid test session id: " + id + " for a total " + testSessions.size() + " sessions.");
		return testSessions.get(id).classpath;
	}
}
