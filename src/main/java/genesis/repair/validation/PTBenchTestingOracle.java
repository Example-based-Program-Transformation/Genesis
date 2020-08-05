package genesis.repair.validation;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;

import org.apache.commons.io.FileUtils;

import genesis.Config;
import genesis.GenesisException;
import genesis.repair.WorkdirManager;

public class PTBenchTestingOracle implements ValidationOracle {

	public final static int FailedPosCaseBatch = 3;

	WorkdirManager manager;
	HashSet<Testcase> failedPosCases;
	
	public PTBenchTestingOracle(WorkdirManager manager) {
		this.manager = manager;
		this.failedPosCases = new HashSet<Testcase>();
	}

	@Override
	public ValidationResult validate(String sourcePath, String newCodeStr, boolean verbose) {
		
		
		return ValidationResult.PASS;
	}

	private List<Testcase> getFailedCases(List<Testcase> passed, Collection<Testcase> a) {
		ArrayList<Testcase> ret = new ArrayList<Testcase>();
		HashSet<Testcase> tmp = new HashSet<Testcase>(passed);
		for (Testcase c : a) {
			if (!tmp.contains(c))
				ret.add(c);
		}
		return ret;
	}
	
	public Map<Testcase, TestResult> runTestcasesForResults(Path extraTestClassPath, List<Testcase> cases) {
		HashMap<Integer, ArrayList<Testcase>> sessionM = new HashMap<Integer, ArrayList<Testcase>>();
		for (Testcase c : cases) {
			int id = manager.getTestSessionId(c.testClass);
			if (id < 0) {
				System.out.println("[WARN]Unable to get test session id for test case: " + c);
				System.out.println("[WARN]Count this testcase failed!");
				continue;
			}
			if (!sessionM.containsKey(id))
				sessionM.put(id, new ArrayList<Testcase>());
			sessionM.get(id).add(c);
		}
		
		HashMap<Testcase, TestResult> ret = new HashMap<>();
		for (Integer id : sessionM.keySet()) {
			String testClassPath = manager.getTestSessionClasspath(id);
			if (extraTestClassPath != null)
				testClassPath = extraTestClassPath.toString() + Config.classPathSep + testClassPath;
			//System.out.println("Testing classpath: " + testClassPath);
			TestcaseExecutor exec = new TestcaseExecutor(testClassPath, sessionM.get(id), manager.getWorkSrcDir());
			exec.run();
			HashMap<Testcase, TestResult> res = null;
			try {
				if (Config.perCaseTimeout == 0)
					res = exec.getResult();
				else
					res = exec.getResult(Config.perCaseTimeout * sessionM.get(id).size());
			}
			catch (InterruptedException e) {
				e.printStackTrace();
				throw new GenesisException("Genesis is interrupted during testing!");
			}
			ret.putAll(res);
		}
		return ret;
	}

	public Map<Testcase, TestResult> runTestcasesForResults(List<Testcase> cases)  {
		return runTestcasesForResults(null, cases);
	}

	public List<Testcase> runTestcases(Path extraTestClassPath, List<Testcase> cases) {
		Map<Testcase, TestResult> res =
			runTestcasesForResults(extraTestClassPath, cases);
		ArrayList<Testcase> ret = new ArrayList<>();
		for (Entry<Testcase, TestResult> e : res.entrySet()) {
			if (e.getValue().getPass()) {
				//System.out.println("Passed: " + e.getKey());
				ret.add(e.getKey());
			}
			else {
				//System.out.println("Failed: " + e.getKey());
			}
		}
		return ret;
	}

	@Override
	public List<Testcase> runTestcases(List<Testcase> cases) {
		return runTestcases(null, cases);
	}

}
