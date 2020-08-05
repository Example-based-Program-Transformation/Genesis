package genesis.repair.localization;

import java.util.List;
import java.util.HashSet;
import java.lang.Thread;
import java.util.Arrays;
import java.io.PrintStream;

import com.gzoltar.lib.instrumentation.testing.junit.JUnitRunner;
import com.gzoltar.lib.instrumentation.testing.TestRunner;
import com.gzoltar.lib.instrumentation.testing.TestResult;
import com.gzoltar.lib.instrumentation.spectra.Spectra;
import com.gzoltar.lib.instrumentation.spectra.FilterTestCasesWithoutCoverage;
import com.gzoltar.lib.instrumentation.components.Component;
import com.gzoltar.lib.instrumentation.transformer.ClassTransformer;
import com.gzoltar.lib.instrumentation.InstrumentingAgent;
import com.gzoltar.lib.instrumentation.InstrumentationStrategy;
import com.gzoltar.lib.client.diag.strategy.CoverageStrategy;

public class GZoltarRunner {
	public static void main(String args[]) {
		List<String> argsL = Arrays.asList(args);
		Spectra spectra = Spectra.getInstance();
		spectra.setGranularity(Component.Granularity.STATEMENT);
		InstrumentingAgent.addTransformer(new ClassTransformer(false, true, true, true, null, new String[]{"*"}, null, new String[]{"*"}, InstrumentationStrategy.RUNTIME_COLLECTOR));
		TestRunner testRunner = new JUnitRunner();
		testRunner.setClassLoader(Thread.currentThread().getContextClassLoader());
		testRunner.setTestCaseTimeout(60);
		testRunner.setTestStrategy(TestRunner.TestStrategy.CLASS);

		HashSet<String> negativeTests = new HashSet<>();
		boolean lookingForNegative = true;

		for (String arg : args) {
			if (arg.equals("--")) {
				lookingForNegative = false;
				continue;
			}
			if (lookingForNegative) {
				negativeTests.add(arg);
			} else {
				for (TestResult t : testRunner.run(arg)) {
					if (t.wasSuccessful() ||
						negativeTests.contains(t.getName())) {
						spectra.addTestResult(t);
					}
				}
			}
		}

		new FilterTestCasesWithoutCoverage().filter(spectra);
		new CoverageStrategy().diagnose(spectra);
		List<Component> cs = spectra.getComponentsOrderedBySuspiciousness("OCHIAI");
		for (Component c : cs) {
			String l = c.getLabel();
			int fileSepIdx = l.indexOf("<");
			String classS = l.substring(fileSepIdx+1, l.indexOf("{"));
			Double suspiciousness = c.getSuspiciousnessValue("OCHIAI");
			// It should be suspicious and not a test
			if (!argsL.contains(classS) && suspiciousness > 0) {
				int packageSepIdx = l.indexOf("[");
				/* Output is package, file name, line number, and
				   suspiciousness */
				String srcPackage = l.substring(0, packageSepIdx);
				String srcFile = l.substring(packageSepIdx+1, fileSepIdx);
				String srcLine = l.substring(l.indexOf("#"));
				System.out.println("__GENESISRESULT:" + srcPackage +"\t" + srcFile + "\t" + srcLine + "\t" + suspiciousness);
			}
		}
	}
}
