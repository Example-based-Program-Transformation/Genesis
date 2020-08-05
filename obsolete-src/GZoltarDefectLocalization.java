package genesis.repair.localization;

import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.nio.file.Paths;

import genesis.Config;
import genesis.GenesisException;
import genesis.repair.WorkdirManager;
import genesis.repair.validation.Testcase;
import genesis.infrastructure.ExecShellCmd;
import com.gzoltar.lib.master.agent.AgentCreator;

public class GZoltarDefectLocalization implements DefectLocalization {

	public static String runnerSEP = "__GENESISRESULT:";

	WorkdirManager manager;

	public GZoltarDefectLocalization(WorkdirManager manager) {
		this.manager = manager;
	}

	class GZoltarWorkerThread extends Thread {

		Process p;
		int exitCode;

		public GZoltarWorkerThread(Process p) {
			super();
			this.p = p;
		}

		@Override
		public void run() {
			try {
				exitCode = p.waitFor();
			}
			catch (InterruptedException ignore) {
			}
		}
	}


	@Override
	public List<SuspiciousLocation> getSuspiciousLocations() {
		HashSet<String> cp = new HashSet<String>();
		cp.add(GZoltarRunner.class.getProtectionDomain().getCodeSource().getLocation().getPath().toString());
		ArrayList<Testcase> cases = new ArrayList<Testcase>(manager.getPositiveCases());
		cases.addAll(manager.getNegativeCases());
		ArrayList<String> caseClasses = new ArrayList<String>();
		for (Testcase c : cases) {
			if (!caseClasses.contains(c.testClass)) {
				caseClasses.add(c.testClass);
				int sessionId = manager.getTestSessionId(c.testClass);
				String caseCp = manager.getTestSessionClasspath(sessionId);
				cp.addAll(Arrays.asList(caseCp.split(Config.classPathSep)));
			}
		}

		ArrayList<String> cmds = new ArrayList<String>();
		cmds.add(Config.jvmCmd);
		cmds.add("-cp");
		cmds.add(String.join(Config.classPathSep, cp));
		cmds.add("-javaagent:" + new AgentCreator().extract().getAbsolutePath());
		cmds.add(GZoltarRunner.class.getName());
		for (Testcase c : manager.getNegativeCases()) {
			cmds.add(c.testClass + "#" + c.testName);
		}
		cmds.add("--");
		cmds.addAll(caseClasses);

		String workSrcDir = manager.getWorkSrcDir();

		ExecShellCmd ecmd = new ExecShellCmd(cmds.toArray(new String[cmds.size()]), workSrcDir, true, false);
		Process p = ecmd.getProcess();
		GZoltarWorkerThread w = new GZoltarWorkerThread(p);
		w.start();
		try {
			String out = ecmd.getOutput();
			ArrayList<SuspiciousLocation> res = new ArrayList<>();
			String[] lines = out.split("\n");
			for (String line : lines) {
				if (line.startsWith(runnerSEP)) {
					String[] parts = line.substring(runnerSEP.length())
					                 .trim()
					                 .split("\t");
					String absPath = manager.getApp()
					                        .guessSrcFile(parts[0], parts[1]);
					if (absPath == null) {
						// The file is not from this project.  Ignore it.
						continue;
					}
					String relPath = Paths.get(workSrcDir)
					                      .toAbsolutePath()
					                      .relativize(Paths.get(absPath))
					                      .toString();
					int ln = Integer.parseInt(parts[2].replaceAll("^#", ""));
					double sp = Double.parseDouble(parts[3]);
					res.add(new SuspiciousLocation(relPath, ln, -1, sp));
				}
			}
			return res;
		} catch (InterruptedException e) {
			e.printStackTrace();
			throw new GenesisException("Defect localization interrupted!");
		} finally {
			p.destroy();
		}
	}

}
